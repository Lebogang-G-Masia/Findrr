"""Model 1 runner: Job Title Expander (Flan-T5 Seq2Seq)."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from findrr.ml.base import IModelRunner
from findrr.ml.exceptions import InferenceExecutionError
from findrr.ml.manifest import load_manifest, verify_artifact_integrity
from findrr.ml.title_constraint import TitleTrieConstraint

logger = logging.getLogger(__name__)


# Deterministic mock title mappings for testing and offline development
MOCK_DOMAIN_EXPANSIONS = {
    "software": [
        "Software Engineer",
        "Backend Developer",
        "Full Stack Developer",
        "Python Engineer",
        "Systems Developer",
        "API Developer",
    ],
    "data": [
        "Data Scientist",
        "Machine Learning Engineer",
        "AI Engineer",
        "Data Analyst",
        "Quantitative Analyst",
    ],
    "devops": [
        "DevOps Engineer",
        "Cloud Platform Engineer",
        "Site Reliability Engineer",
        "Infrastructure Engineer",
    ],
    "product": [
        "Product Manager",
        "Technical Product Manager",
        "Product Owner",
        "Agile Project Manager",
    ],
}


class MockTitleExpanderRunner(IModelRunner):
    """Explicit test and offline mock runner for Model 1 (ML-001)."""

    def __init__(self, version: str = "1.0.0-mock"):
        self._version = version
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("Loaded MOCK Model 1 (Title Expander)")

    def unload(self) -> None:
        self._loaded = False
        logger.info("Unloaded MOCK Model 1 (Title Expander)")

    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def version(self) -> str:
        return self._version

    def expand(
        self,
        generalized_title: str,
        skills: List[str],
        seniority: Optional[str] = None,
    ) -> List[str]:
        """Generate deterministic alternative titles based on title text and skills."""
        if not self.is_loaded():
            self.load()

        title_lower = generalized_title.lower()
        candidates: List[str] = []

        # Find matching cluster
        matched_cluster = None
        for key in MOCK_DOMAIN_EXPANSIONS:
            if key in title_lower:
                matched_cluster = key
                break

        if not matched_cluster:
            # Check skills
            skills_str = " ".join(skills).lower()
            for key in MOCK_DOMAIN_EXPANSIONS:
                if key in skills_str:
                    matched_cluster = key
                    break

        if not matched_cluster:
            matched_cluster = "software"

        for base in MOCK_DOMAIN_EXPANSIONS[matched_cluster]:
            if seniority and not base.lower().startswith(seniority.lower()):
                candidate = f"{seniority} {base}"
            else:
                candidate = base
            if candidate.lower() != generalized_title.lower() and candidate not in candidates:
                candidates.append(candidate)

        return candidates[:6]


class TitleExpanderRunner(IModelRunner):
    """Production runner loading verified PyTorch / HuggingFace Flan-T5 artifacts."""

    def __init__(self, artifact_dir: Path, version: str = "1.0.0"):
        self.artifact_dir = artifact_dir
        self._version = version
        self._model = None
        self._tokenizer = None
        self._constraint: Optional[TitleTrieConstraint] = None
        self._max_new_tokens = 64
        self._max_titles = 5

    def load(self) -> None:
        """Verify integrity and load model into memory."""
        manifest_path = self.artifact_dir / "manifest.json"
        manifest = load_manifest(manifest_path)
        verify_artifact_integrity(manifest, self.artifact_dir)

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            torch.set_num_threads(4)  # Cap CPU inference threads
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.artifact_dir))
            self._model = AutoModelForSeq2SeqLM.from_pretrained(str(self.artifact_dir))
            self._model.eval()
            logger.info("Successfully loaded verified Model 1 from %s", self.artifact_dir)
        except ImportError as err:
            raise RuntimeError(
                f"Required ML dependencies missing to load real Model 1: {err}. "
                "Ensure torch and transformers are installed."
            ) from err

        # D-007: decoding is constrained to the dictionary shipped in the verified bundle.
        prep_path = self.artifact_dir / "preprocess_config.json"
        if prep_path.exists():
            prep = json.loads(prep_path.read_text(encoding="utf-8"))
            self._max_new_tokens = int(prep.get("max_new_tokens", self._max_new_tokens))
            self._max_titles = int(prep.get("max_titles", self._max_titles))
        titles = json.loads((self.artifact_dir / "titles.json").read_text(encoding="utf-8"))
        self._constraint = TitleTrieConstraint(titles, self._tokenizer, self._max_titles)
        logger.info(
            "Model 1 decoding constrained to %d dictionary titles", len(self._constraint.titles)
        )

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._constraint = None
        logger.info("Unloaded Model 1 from memory")

    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def version(self) -> str:
        return self._version

    def expand(
        self,
        generalized_title: str,
        skills: List[str],
        seniority: Optional[str] = None,
    ) -> List[str]:
        """Execute sequence-to-sequence title expansion."""
        if not self.is_loaded():
            self.load()

        import torch

        # Max 5 skills, matching MAX_SKILLS in the training notebook.
        skills_str = ", ".join(skills[:5]) if skills else "general"
        # Must match the level vocabulary in notebooks/01_train_title_expander.ipynb.
        sen_str = (seniority or "ANY").upper()
        prompt = f"expand titles: {generalized_title} | skills: {skills_str} | level: {sen_str}"

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            max_length=128,
            truncation=True,
        )

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self._max_new_tokens,
                num_beams=2,
                do_sample=False,
                repetition_penalty=1.2,
                prefix_allowed_tokens_fn=self._constraint.prefix_allowed_tokens_fn(
                    self._model.config.decoder_start_token_id
                ),
            )

        titles = self._constraint.complete_titles(outputs[0].tolist(), self._tokenizer)
        if not titles:
            raise InferenceExecutionError("Model 1 produced no complete dictionary title.")
        primary = generalized_title.strip().lower()
        return [t for t in titles if t.lower() != primary]
