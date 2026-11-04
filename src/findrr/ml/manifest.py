"""Model manifest schema and cryptographic SHA-256 integrity verifier (Module 9)."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from findrr.ml.exceptions import ModelArtifactMissingError, ModelIntegrityError


class ModelManifest(BaseModel):
    """Schema representing an exported model manifest."""

    model_id: str = Field(..., description="Unique model ID (e.g., ML-001)")
    model_name: str = Field(..., description="Canonical model name")
    version: str = Field(..., description="Semantic model version (e.g., 1.0.0)")
    architecture: str = Field(..., description="Base architecture or checkpoint")
    export_date: str = Field(..., description="ISO-8601 creation timestamp")
    files: Dict[str, str] = Field(..., description="Mapping of relative filename to SHA-256 hex")
    evaluation_summary: Dict[str, float] = Field(
        default_factory=dict, description="Summary evaluation metrics"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional hyperparameter or runtime metadata"
    )


def compute_sha256(file_path: Path) -> str:
    """Calculate the cryptographic SHA-256 digest of a file in 64 KiB chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_manifest(manifest_path: Path) -> ModelManifest:
    """Load and parse manifest.json from disk."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at '{manifest_path}'.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ModelManifest(**data)


def verify_artifact_integrity(manifest: ModelManifest, artifact_dir: Path) -> None:
    """Verify presence and SHA-256 checksums of all model files declared in manifest.

    Raises:
        ModelArtifactMissingError: If any required file is missing.
        ModelIntegrityError: If any file's computed hash mismatches the manifest.
    """
    missing_files = []
    for file_name in manifest.files.keys():
        file_path = artifact_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)

    if missing_files:
        raise ModelArtifactMissingError(
            model_id=manifest.model_id,
            missing_files=missing_files,
            path=str(artifact_dir),
        )

    for file_name, expected_hash in manifest.files.items():
        file_path = artifact_dir / file_name
        actual_hash = compute_sha256(file_path)
        if actual_hash.lower() != expected_hash.lower():
            raise ModelIntegrityError(
                model_id=manifest.model_id,
                file_name=file_name,
                expected_hash=expected_hash,
                actual_hash=actual_hash,
            )
