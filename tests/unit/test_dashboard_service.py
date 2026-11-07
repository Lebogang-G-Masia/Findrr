"""Unit tests for DashboardService (Module 7, US-016, FR-025)."""

import sqlite3

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    ApplicationRepository,
    PostingRepository,
    ProfileRepository,
)
from findrr.models.application import ApplicationStatus
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import UserProfile
from findrr.services.dashboard_service import DashboardService


@pytest.fixture
def db_conn(tmp_path) -> sqlite3.Connection:
    db_file = tmp_path / "test_dash.db"
    conn = get_connection(str(db_file))
    init_db(conn)
    return conn


@pytest.fixture
def dash_env(db_conn: sqlite3.Connection):
    prof_repo = ProfileRepository(db_conn)
    post_repo = PostingRepository(db_conn)
    app_repo = ApplicationRepository(db_conn)

    profile = UserProfile(
        id="user-dash-1",
        full_name="Alex Dashboard",
        email="alex@dash.example.com",
    )
    prof_repo.save_profile(profile)

    p1 = JobPosting(
        id="post-d1",
        title="Backend Engineer",
        company="AlphaCorp",
        description="Python role",
        source_url="https://alpha.example.com/1",
        content_hash="h1" + "0" * 62,
        status=PostingAvailability.ACTIVE,
    )
    p2 = JobPosting(
        id="post-d2",
        title="Frontend Engineer",
        company="AlphaCorp",
        description="React role",
        source_url="https://alpha.example.com/2",
        content_hash="h2" + "0" * 62,
        status=PostingAvailability.CLOSED,
    )
    p3 = JobPosting(
        id="post-d3",
        title="DevOps Engineer",
        company="BetaTech",
        description="Linux role",
        source_url="https://beta.example.com/1",
        content_hash="h3" + "0" * 62,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(p1)
    post_repo.save_posting(p2)
    post_repo.save_posting(p3)

    svc = DashboardService(
        application_repo=app_repo,
        posting_repo=post_repo,
        profile_repo=prof_repo,
    )
    return svc, profile, [p1, p2, p3], app_repo


def test_dashboard_metrics_empty_pipeline(dash_env):
    svc, profile, postings, _ = dash_env
    metrics = svc.get_dashboard_metrics(profile_id=profile.id)

    assert metrics.total_postings == 3
    assert metrics.active_postings == 2
    assert metrics.closed_postings == 1
    assert metrics.unique_companies == 2
    assert metrics.submitted_count == 0
    assert metrics.interview_rate_pct == 0.0
    assert metrics.offer_rate_pct == 0.0
    assert metrics.pipeline_counts["TOTAL"] == 0
    assert len(metrics.recent_activity) == 0


def test_dashboard_metrics_with_pipeline_conversion(dash_env):
    svc, profile, postings, app_repo = dash_env

    # 1. Create applications in different stages
    app1 = app_repo.create_or_get_application(profile.id, postings[0].id)
    app_repo.update_status(app1.id, ApplicationStatus.APPLIED, notes="Submitted application")

    app2 = app_repo.create_or_get_application(profile.id, postings[1].id)
    app_repo.update_status(
        app2.id, ApplicationStatus.INTERVIEWING, notes="Technical screen scheduled"
    )

    app3 = app_repo.create_or_get_application(profile.id, postings[2].id)
    app_repo.update_status(app3.id, ApplicationStatus.SAVED, notes="Preparing CV")

    metrics = svc.get_dashboard_metrics(profile_id=profile.id)

    # 2 applications submitted (1 APPLIED + 1 INTERVIEWING)
    assert metrics.submitted_count == 2
    # 1 interviewing out of 2 submitted = 50.0%
    assert metrics.interview_rate_pct == 50.0
    assert metrics.offer_rate_pct == 0.0
    assert metrics.pipeline_counts["APPLIED"] == 1
    assert metrics.pipeline_counts["INTERVIEWING"] == 1
    assert metrics.pipeline_counts["SAVED"] == 1
    assert metrics.pipeline_counts["TOTAL"] == 3

    assert len(metrics.recent_activity) == 3
    titles = [a["title"] for a in metrics.recent_activity]
    assert "Backend Engineer" in titles
    assert "Frontend Engineer" in titles
