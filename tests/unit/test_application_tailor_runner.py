"""Unit tests for Model 3 Application Tailor Runner (Module 9, ML-003)."""

from findrr.ml.application_tailor_runner import (
    MockApplicationTailorRunner,
    create_application_tailor_runner,
)
from findrr.services.inference_service import InferenceService


def test_mock_application_tailor_runner_lifecycle():
    runner = MockApplicationTailorRunner()
    assert runner.model_id == "ML-003"
    assert not runner.is_loaded()

    runner.load()
    assert runner.is_loaded()

    runner.unload()
    assert not runner.is_loaded()


def test_mock_application_tailor_runner_fact_grounding():
    runner = MockApplicationTailorRunner()
    target_role = "Backend Engineer"
    company = "OmniTech"
    job_requirements = ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"]
    verified_facts = [
        "Built REST APIs using Python and FastAPI for 3 years",
        "Managed PostgreSQL clusters",
        "Packaged microservices with Docker",
    ]

    res = runner.generate_statement(
        target_role=target_role,
        company=company,
        job_requirements=job_requirements,
        verified_user_facts=verified_facts,
    )

    assert "summary_statement" in res
    assert "Backend Engineer" in res["summary_statement"]
    assert "OmniTech" in res["summary_statement"]
    assert "matched_skills" in res
    assert "missing_skills" in res

    # Grounding assertion: matched skills must be in verified facts
    matched = res["matched_skills"]
    assert "python" in matched
    assert "fastapi" in matched
    assert "postgresql" in matched
    assert "docker" in matched
    # Kubernetes is not in verified facts, so must be in missing_skills
    assert "kubernetes" not in matched
    assert "Kubernetes" in res["missing_skills"]
    assert res["is_mock"] is True


def test_create_application_tailor_runner_factory():
    runner = create_application_tailor_runner(force_mock=True)
    assert isinstance(runner, MockApplicationTailorRunner)


def test_inference_service_tailor_statement():
    inf_service = InferenceService(force_mock=True)
    res = inf_service.tailor_statement(
        target_role="Data Engineer",
        company="DataFlow Inc",
        job_requirements=["Python", "SQL", "Snowflake"],
        verified_user_facts=["Constructed ETL pipelines using Python and SQL"],
    )

    assert "summary_statement" in res
    assert "Data Engineer" in res["summary_statement"]
    assert "DataFlow Inc" in res["summary_statement"]
    assert "python" in res["matched_skills"]
    assert "sql" in res["matched_skills"]
    assert "Snowflake" in res["missing_skills"]


# --- Real (ONNX) runner contract tests, with a fake session and tokenizer (no model weights) ---

import json  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from findrr.ml.application_tailor_runner import ONNXApplicationTailorRunner  # noqa: E402
from findrr.ml.exceptions import InferenceExecutionError  # noqa: E402
from findrr.ml.manifest import compute_sha256  # noqa: E402

FACTS = ["Built REST APIs using Python and FastAPI", "Managed PostgreSQL clusters"]


def _artifact_dir(tmp_path):
    d = tmp_path / "application-tailor" / "v1.0.0"
    d.mkdir(parents=True)
    (d / "model.onnx").write_bytes(b"fake")
    (d / "manifest.json").write_text(
        json.dumps(
            {
                "model_id": "ML-003",
                "model_name": "application-tailor",
                "version": "1.0.0",
                "architecture": "test",
                "export_date": "2026-11-26T00:00:00Z",
                "files": {"model.onnx": compute_sha256(d / "model.onnx")},
            }
        )
    )
    return d


class _FakeTokenizer:
    eos_token_id = 0
    unk_token_id = 3

    def __init__(self, reply: str):
        self.reply_ids = [100 + i for i in range(len(reply))]
        self.reply = reply

    def __call__(self, text, return_tensors=None):
        return {"input_ids": np.array([[5, 6, 7]], dtype=np.int64)}

    def convert_tokens_to_ids(self, tok):
        return 1  # <|im_end|>

    def decode(self, ids, skip_special_tokens=True):
        return self.reply[: len(list(ids))]


class _FakeSession:
    """Emits one reply token per step, then the <|im_end|> stop token."""

    def __init__(self, n_reply_tokens: int, vocab: int = 2000):
        self.n = n_reply_tokens
        self.vocab = vocab
        self.calls = 0

    def run(self, _outputs, feeds):
        seq = feeds["input_ids"]
        generated = seq.shape[1] - 3
        logits = np.zeros((1, seq.shape[1], self.vocab), dtype=np.float32)
        nxt = 100 + generated if generated < self.n else 1
        logits[0, -1, nxt] = 1.0
        self.calls += 1
        return [logits]


def _runner(tmp_path, reply):
    r = ONNXApplicationTailorRunner(_artifact_dir(tmp_path))
    r._tokenizer = _FakeTokenizer(reply)
    r._session = _FakeSession(len(reply))
    r._loaded = True
    return r


def test_onnx_runner_reads_manifest_from_directory(tmp_path):
    r = ONNXApplicationTailorRunner(_artifact_dir(tmp_path))
    assert r.version == "1.0.0" and r.is_mock is False


def test_onnx_runner_generates_autoregressively_until_stop(tmp_path):
    reply = json.dumps({"summary_statement": "Built REST APIs.", "matched_skills": ["python"]})
    r = _runner(tmp_path, reply)
    out = r.generate_statement("Backend Engineer", "Acme", ["Python"], FACTS)
    assert out["matched_skills"] == ["python"]
    assert out["is_mock"] is False
    assert r._session.calls == len(reply) + 1  # one step per token, plus the stop step


@pytest.mark.parametrize(
    "reply, match",
    [
        ("not json", "not valid JSON"),
        (json.dumps({"summary_statement": "x"}), "schema"),
        (json.dumps({"summary_statement": "x", "matched_skills": ["kubernetes"]}), "not present"),
    ],
)
def test_onnx_runner_raises_instead_of_falling_back_to_mock(tmp_path, reply, match):
    r = _runner(tmp_path, reply)
    with pytest.raises(InferenceExecutionError, match=match):
        r.generate_statement("Backend Engineer", "Acme", ["Python"], FACTS)


def test_onnx_runner_requires_facts(tmp_path):
    r = _runner(tmp_path, "{}")
    with pytest.raises(InferenceExecutionError, match="verified fact"):
        r.generate_statement("Backend Engineer", "Acme", ["Python"], [])


def test_mock_runner_adds_no_unverified_wording():
    runner = MockApplicationTailorRunner()
    res = runner.generate_statement("Analyst", "Acme", ["SQL"], ["Wrote SQL"])
    text = res["summary_statement"].lower()
    for phrase in ("dedicated", "achievements", "core competencies", "rigor"):
        assert phrase not in text
