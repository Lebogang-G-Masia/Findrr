"""Model 3 runner: Application Tailoring Assistant (Qwen2.5/Flan-T5 ONNX)."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from findrr.ml.base import IModelRunner
from findrr.ml.exceptions import InferenceExecutionError
from findrr.ml.manifest import load_manifest, verify_artifact_integrity

logger = logging.getLogger(__name__)


class MockApplicationTailorRunner(IModelRunner):
    """Explicit test and offline mock runner for Model 3 (ML-003)."""

    def __init__(self, version: str = "1.0.0-mock"):
        self._version = version
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("Loaded MOCK Model 3 (Application Tailor)")

    def unload(self) -> None:
        self._loaded = False
        logger.info("Unloaded MOCK Model 3 (Application Tailor)")

    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_id(self) -> str:
        return "ML-003"

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def version(self) -> str:
        return self._version

    def generate_statement(
        self,
        target_role: str,
        company: str,
        job_requirements: List[str],
        verified_user_facts: List[str],
    ) -> Dict[str, Any]:
        """Generate fact-grounded summary statement strictly from verified facts."""
        facts_text = " ".join(verified_user_facts).lower()
        matched: List[str] = []
        for req in job_requirements:
            r_clean = req.strip().lower()
            if r_clean in facts_text and r_clean not in matched:
                matched.append(r_clean)

        summary = f"Applying for the {target_role} position at {company}."
        if matched:
            summary += " Verified facts mention: " + ", ".join(matched[:4]) + "."
        return {
            "summary_statement": summary,
            "matched_skills": matched,
            "missing_skills": [r for r in job_requirements if r.lower() not in matched],
            "model_version": self._version,
            "is_mock": True,
        }


# Must match the system prompt used in notebooks/03_train_application_tailor.ipynb.
SYSTEM_PROMPT = (
    "You are an application tailoring assistant. You generate professional statements "
    "strictly grounded in verified facts. Never fabricate skills or experience."
)
DEFAULT_MAX_NEW_TOKENS = 256


class ONNXApplicationTailorRunner(IModelRunner):
    """Production runner for an integrity-verified ONNX export of Model 3.

    Generation is greedy and autoregressive over a full-sequence ONNX graph
    (``input_ids`` -> ``logits``). Invalid or ungrounded output raises
    ``InferenceExecutionError``; it is never replaced by MOCK output.
    """

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.manifest = load_manifest(self.model_dir / "manifest.json")
        self._version = self.manifest.version
        self._loaded = False
        self._session = None
        self._tokenizer = None
        self._max_new_tokens = DEFAULT_MAX_NEW_TOKENS

    def load(self) -> None:
        if self._loaded:
            return

        verify_artifact_integrity(self.manifest, self.model_dir)

        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
        except ImportError as err:
            raise RuntimeError(
                f"Required ONNX / tokenizer dependencies missing for Model 3: {err}. "
                "Install the 'ml' extra."
            ) from err

        config_path = self.model_dir / "config.json"
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                self._max_new_tokens = int(cfg.get("max_generation_length", self._max_new_tokens))
            except (ValueError, TypeError) as err:
                logger.warning("Ignoring unreadable Model 3 config.json: %s", err)

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(
            str(self.model_dir / "model.onnx"),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        self._loaded = True
        logger.info("Loaded Model 3 (Application Tailor) from %s", self.model_dir)

    def unload(self) -> None:
        self._session = None
        self._tokenizer = None
        self._loaded = False
        logger.info("Unloaded Model 3 (Application Tailor)")

    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_id(self) -> str:
        return "ML-003"

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def version(self) -> str:
        return self._version

    @staticmethod
    def build_prompt(
        target_role: str, company: str, job_requirements: List[str], verified_user_facts: List[str]
    ) -> str:
        user_payload = {
            "target_role": target_role,
            "company": company,
            "job_requirements": job_requirements,
            "verified_user_facts": verified_user_facts,
        }
        return (
            f"<|im_start|>system\n{SYSTEM_PROMPT}\n<|im_end|>\n"
            f"<|im_start|>user\n{json.dumps(user_payload)}\n<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    def _stop_token_ids(self) -> set:
        ids = set()
        if self._tokenizer.eos_token_id is not None:
            ids.add(int(self._tokenizer.eos_token_id))
        im_end = self._tokenizer.convert_tokens_to_ids("<|im_end|>")
        if isinstance(im_end, int) and im_end >= 0 and im_end != self._tokenizer.unk_token_id:
            ids.add(im_end)
        return ids

    def _generate_greedy(self, prompt: str) -> str:
        import numpy as np

        input_ids = self._tokenizer(prompt, return_tensors="np")["input_ids"].astype(np.int64)
        prompt_len = input_ids.shape[1]
        stop_ids = self._stop_token_ids()
        for _ in range(self._max_new_tokens):
            logits = self._session.run(None, {"input_ids": input_ids})[0]
            next_id = int(logits[0, -1].argmax())
            if next_id in stop_ids:
                break
            input_ids = np.concatenate([input_ids, np.array([[next_id]], dtype=np.int64)], axis=1)
        return self._tokenizer.decode(input_ids[0, prompt_len:], skip_special_tokens=True)

    def generate_statement(
        self,
        target_role: str,
        company: str,
        job_requirements: List[str],
        verified_user_facts: List[str],
    ) -> Dict[str, Any]:
        """Generate a statement with the real model; raise on invalid or ungrounded output."""
        if not verified_user_facts:
            raise InferenceExecutionError(
                "Model 3 requires at least one verified fact; none were supplied."
            )
        if not self._loaded:
            self.load()

        prompt = self.build_prompt(target_role, company, job_requirements, verified_user_facts)
        gen_text = self._generate_greedy(prompt).strip()
        return self.validate_output(gen_text, verified_user_facts, self._version)

    @staticmethod
    def validate_output(
        gen_text: str, verified_user_facts: List[str], version: str
    ) -> Dict[str, Any]:
        """Parse model output and enforce schema and fact grounding (spec sections 3 and 12)."""
        try:
            parsed = json.loads(gen_text)
        except (ValueError, TypeError) as err:
            logger.error("Model 3 produced non-JSON output (%d chars)", len(gen_text))
            raise InferenceExecutionError(f"Model 3 output is not valid JSON: {err}") from err

        if (
            not isinstance(parsed, dict)
            or not isinstance(parsed.get("summary_statement"), str)
            or not isinstance(parsed.get("matched_skills"), list)
        ):
            raise InferenceExecutionError(
                "Model 3 output does not match the schema "
                "{summary_statement: str, matched_skills: list}."
            )

        facts_text = " ".join(verified_user_facts).lower()
        ungrounded = [
            s for s in parsed["matched_skills"] if str(s).strip().lower() not in facts_text
        ]
        if ungrounded:
            logger.error("Model 3 claimed skills absent from verified facts: %s", ungrounded)
            raise InferenceExecutionError(
                f"Model 3 output claims skills not present in verified facts: {ungrounded}"
            )

        parsed["model_version"] = version
        parsed["is_mock"] = False
        return parsed


def create_application_tailor_runner(
    model_dir: Optional[Path] = None, force_mock: bool = False
) -> IModelRunner:
    """Factory creating appropriate Model 3 runner based on environment and artifacts."""
    mock_env = os.environ.get("FINDRR_MOCK_INFERENCE", "false").lower() in ("true", "1")
    if force_mock or mock_env:
        return MockApplicationTailorRunner()

    target_dir = model_dir or Path("models/application-tailor/v1.0.0")
    if not target_dir.exists() or not (target_dir / "manifest.json").exists():
        logger.warning(
            "Model 3 artifacts not found at %s. Using explicitly labelled MOCK runner.",
            target_dir,
        )
        return MockApplicationTailorRunner()

    return ONNXApplicationTailorRunner(target_dir)
