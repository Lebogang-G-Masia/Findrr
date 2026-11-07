"""Integration tests for findrr apply status CLI subcommand (Module 6, US-015, FR-023, FR-024)."""

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
from findrr.models.profile import UserProfile


@pytest.fixture
def app_status_env(tmp_path):
    db_file = tmp_path / "findrr_status_cli_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)

    prof_repo = ProfileRepository(conn)
    post_repo = PostingRepository(conn)
    app_repo = ApplicationRepository(conn)

    profile = UserProfile(
        id="user-stat-cli",
        full_name="Morgan Hunter",
        email="morgan@hunter.example.com",
    )
    prof_repo.save_profile(profile)

    posting = JobPosting(
        id="post-stat-1",
        title="Site Reliability Engineer",
        company="GlobalScale",
        description="Kubernetes, Linux, Go",
        source_url="https://globalscale.example.com/jobs/1",
        content_hash="s1" + "0" * 62,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(posting)

    app = app_repo.create_or_get_application(profile.id, posting.id)
    return str(db_file), profile, posting, app


def test_cli_apply_status_flow(app_status_env):
    db_path, _, _, app = app_status_env

    # 1. Update status to SAVED with note
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(
            [
                "--db-path",
                db_path,
                "apply",
                "status",
                app.id,
                "SAVED",
                "--notes",
                "Reviewing resume",
            ]
        )

    assert exit_code == 0
    out = captured_out.getvalue()
    assert "Application Status Updated (Module 6)" in out
    assert "SAVED" in out
    assert "Reviewing resume" in out

    # 2. Update status to APPLIED with metadata
    captured_out2 = StringIO()
    with patch("sys.stdout", captured_out2):
        exit_code = main(
            [
                "--db-path",
                db_path,
                "apply",
                "status",
                app.id,
                "APPLIED",
                "--applied-at",
                "2026-11-07",
                "--contact-person",
                "Alice Recruiter",
                "--contact-email",
                "alice@globalscale.com",
                "--notes",
                "Submitted directly via careers site",
            ]
        )

    assert exit_code == 0
    out2 = captured_out2.getvalue()
    assert "APPLIED" in out2
    assert "2026-11-07" in out2
    assert "Alice Recruiter <alice@globalscale.com>" in out2
    # Verify notes append
    assert "Reviewing resume" in out2
    assert "Submitted directly via careers site" in out2


def test_cli_apply_status_invalid_date(app_status_env):
    db_path, _, _, app = app_status_env

    captured_err = StringIO()
    with patch("sys.stderr", captured_err):
        exit_code = main(
            [
                "--db-path",
                db_path,
                "apply",
                "status",
                app.id,
                "APPLIED",
                "--applied-at",
                "invalid-date",
            ]
        )

    assert exit_code == 1
    assert "Invalid applied-at date format" in captured_err.getvalue()


def test_cli_apply_status_nonexistent_app(app_status_env):
    db_path, _, _, _ = app_status_env

    captured_err = StringIO()
    with patch("sys.stderr", captured_err):
        exit_code = main(["--db-path", db_path, "apply", "status", "nonexistent-id", "SAVED"])

    assert exit_code == 1
    assert "not found" in captured_err.getvalue()
