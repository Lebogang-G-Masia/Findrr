"""Integration tests for ApplicationRepository (Module 5 & 6, FR-020, FR-021)."""

import sqlite3

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    ApplicationRepository,
    PostingRepository,
    ProfileRepository,
)
from findrr.models.application import (
    ApplicationDocument,
    ApplicationStatus,
    DocumentType,
)
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import UserProfile


@pytest.fixture
def db_conn(tmp_path) -> sqlite3.Connection:
    db_file = tmp_path / "test_app_repo.db"
    conn = get_connection(db_file)
    init_db(conn)
    return conn


@pytest.fixture
def seed_data(db_conn: sqlite3.Connection):
    prof_repo = ProfileRepository(db_conn)
    post_repo = PostingRepository(db_conn)

    profile = UserProfile(
        id="user-repo-1",
        full_name="Taylor Swift",
        email="taylor@example.com",
    )
    prof_repo.save_profile(profile)

    posting = JobPosting(
        id="post-repo-1",
        title="Lead Sound Engineer",
        company="SoundLabs",
        description="Audio engineering role.",
        source_url="https://soundlabs.example.com/jobs/1",
        content_hash="c" * 64,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(posting)

    return profile, posting


def test_create_and_get_application(db_conn: sqlite3.Connection, seed_data):
    profile, posting = seed_data
    repo = ApplicationRepository(db_conn)

    # First creation
    app1 = repo.create_or_get_application(profile.id, posting.id)
    assert app1.id is not None
    assert app1.profile_id == profile.id
    assert app1.job_posting_id == posting.id
    assert app1.status == ApplicationStatus.DISCOVERED

    # Idempotent get
    app2 = repo.create_or_get_application(profile.id, posting.id)
    assert app2.id == app1.id

    # Get by ID
    fetched = repo.get_application(app1.id)
    assert fetched is not None
    assert fetched.id == app1.id

    # Get by profile & posting
    fetched_pair = repo.get_by_profile_and_posting(profile.id, posting.id)
    assert fetched_pair is not None
    assert fetched_pair.id == app1.id


def test_update_application_status(db_conn: sqlite3.Connection, seed_data):
    profile, posting = seed_data
    repo = ApplicationRepository(db_conn)

    app = repo.create_or_get_application(profile.id, posting.id)
    assert app.status == ApplicationStatus.DISCOVERED

    updated = repo.update_status(
        app.id,
        status=ApplicationStatus.SAVED,
        notes="Tailored CV generated. Ready for submission.",
    )
    assert updated.status == ApplicationStatus.SAVED
    assert "Tailored CV generated. Ready for submission." in updated.notes

    # Transition to APPLIED with metadata
    applied = repo.update_status(
        app.id,
        status=ApplicationStatus.APPLIED,
        notes="Confirmed direct submission",
        contact_person="HR Team",
        contact_email="hr@soundlabs.com",
    )
    assert applied.status == ApplicationStatus.APPLIED
    assert applied.applied_at is not None
    assert applied.contact_person == "HR Team"
    assert applied.contact_email == "hr@soundlabs.com"
    assert "Confirmed direct submission" in applied.notes
    assert "Tailored CV generated" in applied.notes


def test_pipeline_and_search_metrics(db_conn: sqlite3.Connection, seed_data):
    profile, posting = seed_data
    app_repo = ApplicationRepository(db_conn)
    post_repo = PostingRepository(db_conn)

    app = app_repo.create_or_get_application(profile.id, posting.id)
    app_repo.update_status(app.id, ApplicationStatus.APPLIED)

    pipeline = app_repo.get_pipeline_summary(profile.id)
    assert pipeline["APPLIED"] == 1
    assert pipeline["TOTAL"] == 1

    search_metrics = post_repo.get_search_metrics()
    assert search_metrics["total_postings"] == 1
    assert search_metrics["active_postings"] == 1
    assert search_metrics["unique_companies"] == 1
    assert len(search_metrics["top_companies"]) == 1


def test_list_applications_for_profile(db_conn: sqlite3.Connection, seed_data):
    profile, posting = seed_data
    repo = ApplicationRepository(db_conn)

    repo.create_or_get_application(profile.id, posting.id)
    apps = repo.list_applications_for_profile(profile.id)
    assert len(apps) == 1
    assert apps[0].profile_id == profile.id


def test_save_and_list_documents(db_conn: sqlite3.Connection, seed_data):
    profile, posting = seed_data
    repo = ApplicationRepository(db_conn)
    app = repo.create_or_get_application(profile.id, posting.id)

    doc = ApplicationDocument(
        application_id=app.id,
        document_type=DocumentType.TAILORED_CV,
        file_path="/path/to/cv.md",
        content_text="# Tailored CV Content",
    )
    saved_doc = repo.save_document(doc)
    assert saved_doc.id == doc.id

    fetched = repo.get_document(doc.id)
    assert fetched is not None
    assert fetched.content_text == "# Tailored CV Content"

    docs = repo.list_documents_for_application(app.id)
    assert len(docs) == 1
    assert docs[0].id == doc.id
    assert docs[0].document_type == DocumentType.TAILORED_CV
