"""Integration tests for Findrr apply CLI subcommands (Module 5, FR-018, FR-019, FR-020)."""

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
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile


@pytest.fixture
def cli_env(tmp_path):
    db_file = tmp_path / "findrr_apply_cli_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)

    prof_repo = ProfileRepository(conn)
    post_repo = PostingRepository(conn)

    profile = UserProfile(
        id="user-cli-1",
        full_name="Sam Fisher",
        email="sam@example.com",
        location="Washington, DC",
        entries=[
            ProfileEntry(
                id="e1",
                profile_id="user-cli-1",
                category=ProfileCategory.SKILL,
                title="Python, Linux, Docker, Network Security",
                is_verified=True,
            ),
            ProfileEntry(
                id="e2",
                profile_id="user-cli-1",
                category=ProfileCategory.EXPERIENCE,
                title="Security Specialist",
                organization="Third Echelon",
                start_date="2020-01",
                description="Deployed secure network monitoring systems using Linux and Python.",
                is_verified=True,
            ),
        ],
    )
    prof_repo.save_profile(profile)

    posting = JobPosting(
        id="post-cli-1",
        title="Security Operations Engineer",
        company="Paladin Cyber",
        description="Looking for Python, Linux, Docker, and Kubernetes security specialist.",
        requirements_extracted=["python", "linux", "docker", "kubernetes"],
        source_url="https://paladin.example.com/jobs/1",
        content_hash="f" * 64,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(posting)

    return str(db_file), profile, posting


def test_cli_apply_analyze_success(cli_env):
    db_path, _, posting = cli_env
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", db_path, "apply", "analyze", posting.id])

    assert exit_code == 0
    out = captured_out.getvalue()
    assert "Job Requirement Gap Analysis" in out
    assert "Security Operations Engineer at Paladin Cyber" in out
    assert "Matching Verified Skills" in out
    assert "python" in out
    assert "linux" in out
    assert "docker" in out
    assert "Missing Prerequisites" in out
    assert "kubernetes" in out


def test_cli_apply_analyze_not_found(cli_env):
    db_path, _, _ = cli_env
    captured_err = StringIO()
    with patch("sys.stderr", captured_err):
        exit_code = main(["--db-path", db_path, "apply", "analyze", "nonexistent-id"])

    assert exit_code == 1
    assert "not found" in captured_err.getvalue()


def test_cli_apply_draft_and_list_and_show(cli_env):
    db_path, profile, posting = cli_env

    # 1. Draft
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", db_path, "apply", "draft", posting.id])

    assert exit_code == 0
    draft_out = captured_out.getvalue()
    assert "Tailored Application Materials Prepared" in draft_out
    assert "Grounding:      VERIFIED" in draft_out
    assert "TAILORED_CV" in draft_out
    assert "COVER_LETTER" in draft_out

    # 2. List
    captured_list = StringIO()
    with patch("sys.stdout", captured_list):
        exit_code = main(["--db-path", db_path, "apply", "list"])

    assert exit_code == 0
    list_out = captured_list.getvalue()
    assert "Prepared Applications (1)" in list_out
    assert posting.id in list_out

    # Extract application id from DB
    conn = get_connection(db_path)
    app_repo = ApplicationRepository(conn)
    apps = app_repo.list_applications_for_profile(profile.id)
    assert len(apps) == 1
    app_id = apps[0].id

    # 3. Show
    captured_show = StringIO()
    with patch("sys.stdout", captured_show):
        exit_code = main(["--db-path", db_path, "apply", "show", app_id])

    assert exit_code == 0
    show_out = captured_show.getvalue()
    assert f"Application Record: {app_id}" in show_out
    assert "TAILORED_CV" in show_out
    assert "COVER_LETTER" in show_out
    assert "Sam Fisher" in show_out


def test_cli_apply_show_not_found(cli_env):
    db_path, _, _ = cli_env
    captured_err = StringIO()
    with patch("sys.stderr", captured_err):
        exit_code = main(["--db-path", db_path, "apply", "show", "nonexistent-app"])

    assert exit_code == 1
    assert "Application 'nonexistent-app' not found" in captured_err.getvalue()
