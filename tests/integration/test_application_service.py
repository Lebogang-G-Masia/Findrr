"""Integration tests for ApplicationService (Module 5, FR-018, FR-019, FR-020)."""

import sqlite3
from pathlib import Path

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    ApplicationRepository,
    PostingRepository,
    ProfileRepository,
)
from findrr.models.application import ApplicationStatus, DocumentType
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import ProfileCategory, ProfileEntry, UserProfile
from findrr.services.application_service import ApplicationService
from findrr.services.document_generator import DocumentGenerator


@pytest.fixture
def db_conn(tmp_path: Path) -> sqlite3.Connection:
    db_file = tmp_path / "test_app_service.db"
    conn = get_connection(str(db_file))
    init_db(conn)
    return conn


@pytest.fixture
def service_env(db_conn: sqlite3.Connection, tmp_path: Path):
    prof_repo = ProfileRepository(db_conn)
    post_repo = PostingRepository(db_conn)
    app_repo = ApplicationRepository(db_conn)

    profile = UserProfile(
        id="user-svc-1",
        full_name="Jordan Lee",
        email="jordan@example.com",
        location="Chicago, IL",
        entries=[
            ProfileEntry(
                id="e1",
                profile_id="user-svc-1",
                category=ProfileCategory.SKILL,
                title="Python, PostgreSQL, Docker",
                is_verified=True,
            ),
            ProfileEntry(
                id="e2",
                profile_id="user-svc-1",
                category=ProfileCategory.EXPERIENCE,
                title="Software Engineer",
                organization="Midwest Data",
                start_date="2022-01",
                description="Built data pipelines using Python and PostgreSQL.",
                is_verified=True,
            ),
        ],
    )
    prof_repo.save_profile(profile)

    posting = JobPosting(
        id="post-svc-1",
        title="Python Data Engineer",
        company="Lakefront Analytics",
        description="Seeking Python and Docker engineer with Kubernetes and PostgreSQL skills.",
        requirements_extracted=["python", "docker", "kubernetes", "postgresql"],
        source_url="https://lakefront.example.com/jobs/1",
        content_hash="d" * 64,
        status=PostingAvailability.ACTIVE,
    )
    post_repo.save_posting(posting)

    docs_dir = tmp_path / "applications"
    doc_gen = DocumentGenerator(storage_dir=docs_dir)

    service = ApplicationService(
        application_repo=app_repo,
        posting_repo=post_repo,
        profile_repo=prof_repo,
        document_generator=doc_gen,
    )

    return service, profile, posting, docs_dir


def test_analyze_requirements(service_env):
    service, profile, posting, _ = service_env
    analysis = service.analyze_requirements(posting.id, profile_id=profile.id)

    assert analysis.posting_id == posting.id
    assert "python" in analysis.matching_skills
    assert "docker" in analysis.matching_skills
    assert "postgresql" in analysis.matching_skills
    assert "kubernetes" in analysis.missing_prerequisites
    assert analysis.match_percentage == 75.0


def test_analyze_requirements_not_found(service_env):
    service, _, _, _ = service_env
    with pytest.raises(ValueError, match="Job posting nonexistent not found"):
        service.analyze_requirements("nonexistent")


def test_prepare_application_generates_documents_and_stores(service_env):
    service, profile, posting, docs_dir = service_env

    app = service.prepare_application(posting.id, profile_id=profile.id)
    assert app.profile_id == profile.id
    assert app.job_posting_id == posting.id

    docs = service.list_documents(app.id)
    assert len(docs) == 2

    types = {d.document_type for d in docs}
    assert DocumentType.TAILORED_CV in types
    assert DocumentType.COVER_LETTER in types

    for d in docs:
        p = Path(d.file_path)
        assert p.exists()
        assert p.is_file()
        assert len(p.read_text(encoding="utf-8")) > 0

    # Verify listing and fetching
    apps = service.list_applications(profile_id=profile.id)
    assert len(apps) == 1
    assert apps[0].id == app.id

    fetched = service.get_application(app.id)
    assert fetched is not None
    assert fetched.id == app.id

    # Update status
    updated = service.update_status(app.id, status=ApplicationStatus.SAVED, notes="Draft ready")
    assert updated.status == ApplicationStatus.SAVED
    assert "Draft ready" in updated.notes
