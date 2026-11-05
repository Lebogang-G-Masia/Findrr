"""Unit tests for InferenceService, runner lifecycles, and candidate filtering."""

import pytest

from findrr.services.inference_service import InferenceService


@pytest.fixture
def inference_service():
    # Force mock mode for fast unit tests without loading 500MB weights
    return InferenceService(force_mock=True)


def test_title_expansion_mock(inference_service):
    res = inference_service.expand_titles(
        generalized_title="Software Developer",
        skills=["Python", "FastAPI", "SQL"],
        seniority="Senior",
    )
    assert res.model_id == "ML-001"
    assert res.is_mock is True
    assert len(res.expanded_titles) > 0
    assert any("Senior" in t for t in res.expanded_titles)


def test_similarity_evaluation_mock(inference_service):
    # Synonymous titles must evaluate high
    res_high = inference_service.evaluate_similarity("Software Developer", "Software Engineer")
    assert res_high.is_mock is True
    assert res_high.similarity_score >= 0.85

    # Distinct titles must evaluate low
    res_low = inference_service.evaluate_similarity("Software Developer", "Dental Assistant")
    assert res_low.similarity_score < 0.30


def test_filter_and_validate_candidates(inference_service):
    primary = "Software Developer"
    candidates = [
        "Software Engineer",  # High relevance (accepted)
        "Backend Developer",  # High relevance (accepted)
        "Software Engineer",  # Duplicate of first accepted (rejected duplicate)
        "Dental Assistant",  # Low relevance (rejected low score)
    ]

    evaluated = inference_service.filter_and_validate_candidates(
        primary_title=primary,
        candidates=candidates,
        relevance_threshold=0.70,
        dedup_threshold=0.88,
    )

    assert len(evaluated) == 4
    statuses = [e.status for e in evaluated]
    assert "ACCEPTED" in statuses
    assert "REJECTED_LOW_SCORE" in statuses
    assert "REJECTED_DUPLICATE" in statuses


def test_model_unloading_lifecycle(inference_service):
    # Trigger loading
    inference_service.expand_titles("Data Scientist", ["Python", "PyTorch"])
    assert "ML-001" in inference_service._runners
    assert inference_service._runners["ML-001"].is_loaded() is True

    # Unload
    inference_service.unload_model("ML-001")
    assert "ML-001" not in inference_service._runners

    # Unload all
    inference_service.evaluate_similarity("A", "B")
    assert "ML-002" in inference_service._runners
    inference_service.unload_all()
    assert len(inference_service._runners) == 0
