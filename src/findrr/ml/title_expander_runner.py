"""Model 1 runner: Job Title Expander (Flan-T5 Seq2Seq)."""

import logging
from pathlib import Path
from typing import List, Optional

from findrr.ml.base import IModelRunner
from findrr.ml.manifest import load_manifest, verify_artifact_integrity

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

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
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

        skills_str = ", ".join(skills[:8]) if skills else "general"
        sen_str = seniority or "Standard"
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
                max_new_tokens=48,
                num_beams=2,
                temperature=0.3,
                repetition_penalty=1.2,
            )

        decoded = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        raw_titles = [t.strip() for t in decoded.split(",") if t.strip()]

        cleaned: List[str] = []
        for t in raw_titles:
            if t.lower() != generalized_title.lower() and t not in cleaned:
                cleaned.append(t)
        return cleaned
