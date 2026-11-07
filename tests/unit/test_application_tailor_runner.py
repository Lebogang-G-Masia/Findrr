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
