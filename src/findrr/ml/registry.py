"""Model registry catalog and artifact location resolver (Module 9)."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from findrr.ml.exceptions import (
    ModelArtifactMissingError,
    ModelIntegrityError,
    ModelNotConfiguredError,
)
from findrr.ml.manifest import load_manifest, verify_artifact_integrity

DEFAULT_MODELS_DIR = Path("models")


class ModelRegistration(BaseModel):
    """Configuration and state for a registered model."""

    model_id: str
    name: str
    active_version: str
    relative_path: str
    purpose: str
    architecture: str
    required_files: List[str] = Field(default_factory=list)


# Authoritative registry metadata reflecting Gate 4 Approved Specifications
CATALOG: Dict[str, ModelRegistration] = {
    "ML-001": ModelRegistration(
        model_id="ML-001",
        name="title-expander",
        active_version="1.0.0",
        relative_path="title-expander/v1.0.0",
        purpose="Generative search term expansion from generalized titles and skills",
        architecture="google/flan-t5-small (Seq2Seq Transformer)",
        required_files=[
            "manifest.json",
            "model.safetensors",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "preprocess_config.json",
        ],
    ),
    "ML-002": ModelRegistration(
        model_id="ML-002",
        name="similarity-evaluator",
        active_version="1.0.0",
        relative_path="similarity-evaluator/v1.0.0",
        purpose="Dense bi-encoder semantic similarity scoring and deduplication",
        architecture="sentence-transformers/all-MiniLM-L6-v2 (ONNX Bi-Encoder)",
        required_files=[
            "manifest.json",
            "model.onnx",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "preprocess_config.json",
        ],
    ),
    "ML-003": ModelRegistration(
        model_id="ML-003",
        name="application-tailor",
        active_version="1.0.0",
        relative_path="application-tailor/v1.0.0",
        purpose="Factual CV tailoring and cover letter draft generation",
        architecture="Qwen2.5-0.5B-Instruct / Flan-T5-base",
        required_files=[
            "manifest.json",
            "model.onnx",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
        ],
    ),
}


class ModelRegistry:
    """Manages active models, locations, manifest checks, and status."""

    def __init__(self, base_models_dir: Optional[Path] = None):
        env_dir = os.getenv("FINDRR_MODELS_DIR")
        self.base_dir = Path(env_dir) if env_dir else (base_models_dir or DEFAULT_MODELS_DIR)

    def get_registration(self, model_id_or_name: str) -> ModelRegistration:
        """Retrieve model registration entry by ID or canonical name."""
        if model_id_or_name in CATALOG:
            return CATALOG[model_id_or_name]
        for reg in CATALOG.values():
            if reg.name == model_id_or_name:
                return reg
        raise ModelNotConfiguredError(
            f"No registered model found for '{model_id_or_name}'. "
            f"Available models: {list(CATALOG.keys())}"
        )

    def list_registrations(self) -> List[ModelRegistration]:
        """List all cataloged model registrations."""
        return list(CATALOG.values())

    def get_artifact_dir(self, model_id_or_name: str) -> Path:
        """Resolve absolute or relative directory for the active model version."""
        reg = self.get_registration(model_id_or_name)
        return self.base_dir / reg.relative_path

    def inspect_model_status(self, model_id_or_name: str) -> Dict[str, Any]:
        """Inspect the current artifact and verification status of a model on disk."""
        reg = self.get_registration(model_id_or_name)
        artifact_dir = self.get_artifact_dir(reg.model_id)
        manifest_path = artifact_dir / "manifest.json"

        status_info: Dict[str, Any] = {
            "model_id": reg.model_id,
            "name": reg.name,
            "version": reg.active_version,
            "path": str(artifact_dir),
            "manifest_exists": manifest_path.exists(),
            "artifacts_present": False,
            "integrity_verified": False,
            "error": None,
        }

        if not manifest_path.exists():
            status_info["error"] = (
                "Manifest missing (model not yet trained or artifacts not copied)."
            )
            return status_info

        try:
            manifest = load_manifest(manifest_path)
            verify_artifact_integrity(manifest, artifact_dir)
            status_info["artifacts_present"] = True
            status_info["integrity_verified"] = True
            status_info["evaluation_summary"] = manifest.evaluation_summary
        except (ModelArtifactMissingError, ModelIntegrityError) as err:
            status_info["error"] = str(err)
        except Exception as exc:
            status_info["error"] = f"Failed to inspect model: {exc}"

        return status_info
