"""Integration tests for PostingRepository in SQLite database (Module 4)."""

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import PostingRepository
from findrr.models.posting import JobPosting, PostingAvailability


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "postings_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)
    return PostingRepository(conn)


def test_save_and_get_posting(repo):
    posting = JobPosting(
        id="post-1",
        search_term_id=None,
        title="Senior Python Engineer",
        company="TechCorp",
        location="Johannesburg",
        description="Great role building distributed Python services.",
        requirements_extracted=["python", "docker", "sql"],
        source_url="https://indeed.com/view/123",
        direct_apply_url="https://techcorp.bamboohr.com/jobs/1",
        content_hash="a" * 64,
        status=PostingAvailability.ACTIVE,
        posting_date="2026-11-01",
    )

    saved = repo.save_posting(posting)
    assert saved.id == "post-1"
    assert saved.company == "TechCorp"

    fetched = repo.get_posting("post-1")
    assert fetched is not None
    assert fetched.title == "Senior Python Engineer"
    assert fetched.requirements_extracted == ["python", "docker", "sql"]
    assert fetched.direct_apply_url == "https://techcorp.bamboohr.com/jobs/1"


def test_get_by_content_hash(repo):
    h = "b" * 64
    posting = JobPosting(
        id="post-2",
        title="Full Stack Engineer",
        company="WebLabs",
        description="React and Node.js development.",
        source_url="https://example.com/job/2",
        content_hash=h,
    )
    repo.save_posting(posting)

    found = repo.get_by_content_hash(h)
    assert found is not None
    assert found.title == "Full Stack Engineer"

    assert repo.get_by_content_hash("nonexistent") is None


def test_save_posting_on_conflict_update(repo):
    h = "c" * 64
    posting1 = JobPosting(
        id="post-orig",
        title="Cloud Engineer",
        company="Skyline",
        description="AWS and Terraform.",
        source_url="https://example.com/1",
        content_hash=h,
        status=PostingAvailability.ACTIVE,
    )
    repo.save_posting(posting1)

    # Re-saving same content_hash updates metadata instead of failing
    posting2 = JobPosting(
        id="post-new",
        title="Senior Cloud Engineer",
        company="Skyline",
        description="AWS, Terraform, and Kubernetes.",
        source_url="https://example.com/2",
        content_hash=h,
        status=PostingAvailability.ACTIVE,
    )
    saved2 = repo.save_posting(posting2)
    assert saved2.title == "Senior Cloud Engineer"
    assert repo.count_postings() == 1


def test_list_and_count_postings(repo):
    for i in range(5):
        repo.save_posting(
            JobPosting(
                id=f"p-{i}",
                search_term_id=None,
                title=f"Engineer {i}",
                company=f"Company {i}",
                description=f"Desc {i}",
                source_url=f"https://example.com/{i}",
                content_hash=f"{i}" * 64,
            )
        )

    assert repo.count_postings() == 5
    all_postings = repo.list_all_postings(limit=10)
    assert len(all_postings) == 5
