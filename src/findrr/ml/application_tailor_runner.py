"""Model 3 runner: Application Tailoring Assistant (Qwen2.5/Flan-T5 ONNX)."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from findrr.ml.base import IModelRunner
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

        matched_str = ", ".join(matched[:4]) if matched else "core competencies"
        summary = (
            f"Dedicated professional targeting the {target_role} position at {company}. "
            f"Offering verified background and practical experience in {matched_str}. "
            "Grounded in technical rigor and verified achievements."
        )
        return {
            "summary_statement": summary,
            "matched_skills": matched,
            "missing_skills": [r for r in job_requirements if r.lower() not in matched],
            "model_version": self._version,
            "is_mock": True,
        }


class ONNXApplicationTailorRunner(IModelRunner):
    """Real ONNX Runtime CPU inference runner for Model 3 (ML-003)."""

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.manifest = load_manifest(self.model_dir)
        self._version = self.manifest.version
        self._loaded = False
        self._session = None
        self._tokenizer = None

    def load(self) -> None:
        if self._loaded:
            return

        verify_artifact_integrity(self.model_dir, self.manifest)

        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer

            model_path = self.model_dir / "model.onnx"
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 4
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._session = ort.InferenceSession(
                str(model_path), sess_options=opts, providers=["CPUExecutionProvider"]
            )
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            self._loaded = True
            logger.info("Loaded Model 3 (Application Tailor) from %s", self.model_dir)
        except Exception as err:
            logger.error("Failed to load Model 3 ONNX session: %s", err)
            raise

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

    def generate_statement(
        self,
        target_role: str,
        company: str,
        job_requirements: List[str],
        verified_user_facts: List[str],
    ) -> Dict[str, Any]:
        """Generate statement using ONNX model."""
        if not self._loaded or not self._session or not self._tokenizer:
            self.load()

        user_payload = {
            "target_role": target_role,
            "company": company,
            "job_requirements": job_requirements,
            "verified_user_facts": verified_user_facts,
        }
        prompt = (
            f"<|im_start|>system\nYou are an application tailoring assistant. "
            f"You generate professional statements strictly grounded in verified facts.<|im_end|>\n"
            f"<|im_start|>user\n{json.dumps(user_payload)}\n<|im_end|>\n<|im_start|>assistant\n"
        )
        inputs = self._tokenizer(prompt, return_tensors="np")
        input_ids = inputs["input_ids"]

        outputs = self._session.run(None, {"input_ids": input_ids})
        logits = outputs[0]
        tokens = logits.argmax(axis=-1)[0]
        gen_text = self._tokenizer.decode(tokens, skip_special_tokens=True)

        try:
            parsed = json.loads(gen_text)
            parsed["model_version"] = self._version
            parsed["is_mock"] = False
            return parsed
        except Exception:
            # Fallback to deterministic fact-grounded response
            return MockApplicationTailorRunner(version=self._version).generate_statement(
                target_role, company, job_requirements, verified_user_facts
            )


def create_application_tailor_runner(
    model_dir: Optional[Path] = None, force_mock: bool = False
) -> IModelRunner:
    """Factory creating appropriate Model 3 runner based on environment and artifacts."""
    mock_env = os.environ.get("FINDRR_MOCK_INFERENCE", "false").lower() in ("true", "1")
    if force_mock or mock_env:
        return MockApplicationTailorRunner()

    target_dir = model_dir or Path("models/application-tailor/v1.0.0")
    if not target_dir.exists() or not (target_dir / "manifest.json").exists():
        logger.info(
            "Model 3 artifacts not found at %s. Falling back to MockApplicationTailorRunner.",
            target_dir,
        )
        return MockApplicationTailorRunner()

    return ONNXApplicationTailorRunner(target_dir)
