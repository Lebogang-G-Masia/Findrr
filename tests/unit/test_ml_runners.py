"""Unit tests for ML runners, integrity checks, and error boundaries."""

import pytest

from findrr.ml.similarity_evaluator_runner import (
    MockSimilarityEvaluatorRunner,
    SimilarityEvaluatorRunner,
)
from findrr.ml.title_expander_runner import (
    MockTitleExpanderRunner,
    TitleExpanderRunner,
)


def test_mock_title_expander_lifecycle():
    runner = MockTitleExpanderRunner(version="1.0.0-test")
    assert runner.is_mock is True
    assert runner.is_loaded() is False
    assert runner.version == "1.0.0-test"

    titles = runner.expand("Data Scientist", ["Python", "PyTorch"], "Senior")
    assert runner.is_loaded() is True
    assert len(titles) > 0
    assert any("Senior" in t for t in titles)

    runner.unload()
    assert runner.is_loaded() is False


def test_mock_similarity_evaluator_lifecycle():
    runner = MockSimilarityEvaluatorRunner(version="1.0.0-test")
    assert runner.is_mock is True
    assert runner.is_loaded() is False

    score = runner.evaluate_pair("Software Developer", "Software Engineer")
    assert runner.is_loaded() is True
    assert score >= 0.85

    batch = runner.evaluate_batch([("A", "B"), ("C", "D")])
    assert len(batch) == 2

    runner.unload()
    assert runner.is_loaded() is False


def test_real_title_expander_fails_on_missing_dir(tmp_path):
    empty_dir = tmp_path / "empty_model"
    empty_dir.mkdir()

    runner = TitleExpanderRunner(artifact_dir=empty_dir)
    with pytest.raises(FileNotFoundError):
        runner.load()


def test_real_similarity_evaluator_fails_on_missing_dir(tmp_path):
    empty_dir = tmp_path / "empty_model"
    empty_dir.mkdir()

    runner = SimilarityEvaluatorRunner(artifact_dir=empty_dir)
    with pytest.raises(FileNotFoundError):
        runner.load()
