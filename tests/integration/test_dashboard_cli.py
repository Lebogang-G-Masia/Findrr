"""Integration tests for Findrr dashboard CLI subcommand (Module 7, US-016, FR-025)."""

from io import StringIO
from unittest.mock import patch

import pytest

from findrr.cli.main import main
from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    ApplicationRepository,
    PostingRepository,
    ProfileRepository,
)
from findrr.models.application import ApplicationStatus
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import UserProfile


@pytest.fixture
def dash_cli_env(tmp_path):
    db_file = tmp_path / "findrr_dash_cli_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)

    prof_repo = ProfileRepository(conn)
    post_repo = PostingRepository(conn)
    app_repo = ApplicationRepository(conn)

    profile = UserProfile(
        id="user-dash-cli",
        full_name="Jordan Metric",
        email="jordan@metric.example.com",
    )
    prof_repo.save_profile(profile)

    p1 = JobPosting(
        id="post-cli-d1",
        title="Senior Cloud Architect",
        company="AeroCloud",
        description="Kubernetes & Terraform",
        source_url="https://aerocloud.example.com/1",
        content_hash="x1" + "0" * 62,
        status=PostingAvailability.ACTIVE,
    )
    p2 = JobPosting(
        id="post-cli-d2",
        title="Platform Engineer",
        company="AeroCloud",
        description="Linux & Docker",
        source_url="https://aerocloud.example.com/2",
        content_hash="x2" + "0" * 62,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(p1)
    post_repo.save_posting(p2)

    app1 = app_repo.create_or_get_application(profile.id, p1.id)
    app_repo.update_status(app1.id, ApplicationStatus.APPLIED, notes="Submitted application")

    return str(db_file), profile, [p1, p2], app1


def test_cli_dashboard_success(dash_cli_env):
    db_path, _, _, _ = dash_cli_env

    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", db_path, "dashboard"])

    assert exit_code == 0
    out = captured_out.getvalue()
    assert "Findrr Job Search & Application Dashboard" in out
    assert "Opportunity Discovery & Search Metrics" in out
    assert "Total Postings Tracked:   2" in out
    assert "Active Postings:          2" in out
    assert "AeroCloud" in out
    assert "Application Pipeline Progression" in out
    assert "Submitted (Applied):  1" in out
    assert "Pipeline Performance & Conversion Rates" in out
    assert "Senior Cloud Architect at AeroCloud" in out


def test_cli_dashboard_empty(tmp_path):
    db_file = tmp_path / "findrr_empty_dash.db"
    conn = get_connection(str(db_file))
    init_db(conn)
    prof_repo = ProfileRepository(conn)
    profile = UserProfile(
        id="user-empty",
        full_name="Empty User",
        email="empty@example.com",
    )
    prof_repo.save_profile(profile)

    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", str(db_file), "dashboard"])

    assert exit_code == 0
    out = captured_out.getvalue()
    assert "Total Postings Tracked:   0" in out
    assert "(No applications prepared yet" in out
