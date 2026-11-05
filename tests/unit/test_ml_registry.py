"""Unit tests for ModelRegistry and artifact catalog."""

import pytest

from findrr.ml.exceptions import ModelNotConfiguredError
from findrr.ml.registry import ModelRegistry


def test_registry_get_registration():
    registry = ModelRegistry()

    m1 = registry.get_registration("ML-001")
    assert m1.name == "title-expander"
    assert m1.active_version == "1.0.0"

    m2 = registry.get_registration("similarity-evaluator")
    assert m2.model_id == "ML-002"

    with pytest.raises(ModelNotConfiguredError):
        registry.get_registration("NON_EXISTENT_MODEL")


def test_registry_list_registrations():
    registry = ModelRegistry()
    models = registry.list_registrations()
    ids = {m.model_id for m in models}
    assert {"ML-001", "ML-002", "ML-003"}.issubset(ids)


def test_registry_inspect_model_uninitialized(tmp_path):
    registry = ModelRegistry(base_models_dir=tmp_path)
    status = registry.inspect_model_status("ML-001")

    assert status["model_id"] == "ML-001"
    assert status["manifest_exists"] is False
    assert status["artifacts_present"] is False
    assert status["integrity_verified"] is False
    assert "Manifest missing" in status["error"]
