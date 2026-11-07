"""Integration tests for Findrr CLI model management and inference commands."""

from io import StringIO
from unittest.mock import patch

import pytest

from findrr.cli.main import main


@pytest.fixture
def test_db_path(tmp_path):
    db_file = tmp_path / "findrr_ml_test.db"
    return str(db_file)


def test_cli_model_list(test_db_path):
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "model", "list"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "ML-001" in output
    assert "title-expander" in output
    assert "ML-002" in output
    assert "similarity-evaluator" in output


def test_cli_model_inspect(test_db_path):
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "model", "inspect", "ML-001"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Model Inspection: ML-001" in output
    assert "title-expander" in output


def test_cli_model_expand(test_db_path):
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(
            [
                "--db-path",
                test_db_path,
                "model",
                "expand",
                "Software Developer",
                "--skills",
                "Python,SQL",
            ]
        )
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Title Expansion for: Software Developer" in output
    assert "ML-001" in output


def test_cli_model_compare(test_db_path):
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(
            [
                "--db-path",
                test_db_path,
                "model",
                "compare",
                "Software Developer",
                "Software Engineer",
            ]
        )
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Semantic Similarity" in output
    assert "Similarity Score:" in output
