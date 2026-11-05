"""Unit tests for ModelManifest, checksum calculations, and integrity checks."""

import hashlib

import pytest

from findrr.ml.exceptions import ModelArtifactMissingError, ModelIntegrityError
from findrr.ml.manifest import (
    ModelManifest,
    compute_sha256,
    load_manifest,
    verify_artifact_integrity,
)


def test_compute_sha256(tmp_path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Findrr Model Artifact Content", encoding="utf-8")

    expected_hash = hashlib.sha256(b"Findrr Model Artifact Content").hexdigest()
    computed_hash = compute_sha256(test_file)

    assert computed_hash == expected_hash


def test_manifest_validation_success(tmp_path):
    artifact_dir = tmp_path / "model_bundle"
    artifact_dir.mkdir()

    weights_file = artifact_dir / "model.safetensors"
    weights_file.write_bytes(b"dummy_weights_data")

    config_file = artifact_dir / "config.json"
    config_file.write_text('{"hidden_dim": 384}', encoding="utf-8")

    manifest = ModelManifest(
        model_id="ML-TEST",
        model_name="test-model",
        version="1.0.0",
        architecture="test-arch",
        export_date="2026-11-04T00:00:00Z",
        files={
            "model.safetensors": compute_sha256(weights_file),
            "config.json": compute_sha256(config_file),
        },
        evaluation_summary={"metric_a": 0.95},
    )

    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    loaded = load_manifest(manifest_path)
    assert loaded.model_id == "ML-TEST"

    # Integrity verification must pass without raising exception
    verify_artifact_integrity(loaded, artifact_dir)


def test_manifest_validation_missing_file(tmp_path):
    artifact_dir = tmp_path / "model_bundle"
    artifact_dir.mkdir()

    config_file = artifact_dir / "config.json"
    config_file.write_text('{"hidden_dim": 384}', encoding="utf-8")

    manifest = ModelManifest(
        model_id="ML-TEST",
        model_name="test-model",
        version="1.0.0",
        architecture="test-arch",
        export_date="2026-11-04T00:00:00Z",
        files={
            "model.safetensors": "a" * 64,  # Missing on disk
            "config.json": compute_sha256(config_file),
        },
    )

    with pytest.raises(ModelArtifactMissingError) as exc_info:
        verify_artifact_integrity(manifest, artifact_dir)

    assert "missing required file(s) [model.safetensors]" in str(exc_info.value)


def test_manifest_validation_corrupted_file(tmp_path):
    artifact_dir = tmp_path / "model_bundle"
    artifact_dir.mkdir()

    weights_file = artifact_dir / "model.safetensors"
    weights_file.write_bytes(b"original_weights")

    valid_hash = compute_sha256(weights_file)

    # Tamper with file
    weights_file.write_bytes(b"tampered_weights")

    manifest = ModelManifest(
        model_id="ML-TEST",
        model_name="test-model",
        version="1.0.0",
        architecture="test-arch",
        export_date="2026-11-04T00:00:00Z",
        files={"model.safetensors": valid_hash},
    )

    with pytest.raises(ModelIntegrityError) as exc_info:
        verify_artifact_integrity(manifest, artifact_dir)

    assert "Model integrity violation" in str(exc_info.value)
    assert exc_info.value.expected_hash == valid_hash
