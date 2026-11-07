"""Integration tests for Findrr search CLI subcommands (Module 4)."""

from io import StringIO
from unittest.mock import patch

import pytest

from findrr.cli.main import main
from findrr.db.connection import get_connection, init_db
from findrr.db.repository import PostingRepository, ProfileRepository, TitleRepository
from findrr.models.posting import JobPosting, PostingAvailability
from findrr.models.profile import UserProfile
from findrr.models.title import GeneralizedTitle


@pytest.fixture
def test_db_path(tmp_path):
    db_file = tmp_path / "findrr_search_cli_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)
    return str(db_file)


def test_cli_search_list_empty(test_db_path):
    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "search", "list"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Discovered Job Postings (0)" in output
    assert "No job postings found in database" in output


def test_cli_search_inspect_not_found(test_db_path):
    captured_err = StringIO()
    with patch("sys.stderr", captured_err):
        exit_code = main(["--db-path", test_db_path, "search", "inspect", "nonexistent-id"])
    assert exit_code == 1
    assert "not found" in captured_err.getvalue()


def test_cli_search_inspect_success(test_db_path):
    conn = get_connection(test_db_path)
    posting_repo = PostingRepository(conn)
    p = JobPosting(
        id="test-post-42",
        title="Lead Platform Architect",
        company="HyperScale Corp",
        location="Johannesburg",
        description="Lead our distributed infrastructure across AWS and Kubernetes.",
        requirements_extracted=["aws", "kubernetes", "python", "terraform"],
        source_url="https://google.com/search?q=hyperscale",
        direct_apply_url="https://jobs.lever.co/hyperscale/42",
        content_hash="d" * 64,
        status=PostingAvailability.ACTIVE,
    )
    posting_repo.save_posting(p)

    captured_out = StringIO()
    with patch("sys.stdout", captured_out):
        exit_code = main(["--db-path", test_db_path, "search", "inspect", "test-post-42"])
    assert exit_code == 0
    output = captured_out.getvalue()
    assert "Lead Platform Architect" in output
    assert "HyperScale Corp" in output
    assert "https://jobs.lever.co/hyperscale/42" in output
    assert "kubernetes" in output


def test_cli_search_run_with_mocked_engine(test_db_path):
    conn = get_connection(test_db_path)
    profile_repo = ProfileRepository(conn)
    title_repo = TitleRepository(conn)

    prof = profile_repo.save_profile(
        UserProfile(
            full_name="Bob Searcher",
            email="bob@example.com",
            location="Cape Town",
        )
    )
    title_repo.save_title(
        GeneralizedTitle(
            profile_id=prof.id,
            primary_title="DevOps Specialist",
            rationale="Automated systems background",
            supporting_skills=["Linux", "Docker"],
        )
    )

    fake_search_page = """
    <html><body>
      <a href="https://target.com/job/101">DevOps Role</a>
    </body></html>
    """
    fake_job_page = """
    <html><body>
      <h1>DevOps Role</h1>
      <div class="company">Target Technologies</div>
      <div class="description">Managing Kubernetes and Linux servers.</div>
      <a href="https://boards.greenhouse.io/target/jobs/1">Apply Direct</a>
    </body></html>
    """

    def fake_fetcher(url: str) -> str:
        if "google.com" in url:
            return fake_search_page
        return fake_job_page

    with patch("findrr.cli.search_cli.JobDiscoveryEngine") as mock_engine_cls:
        from findrr.search.engine import JobDiscoveryEngine

        real_engine_with_fake_fetcher = JobDiscoveryEngine(page_fetcher=fake_fetcher)
        mock_engine_cls.return_value = real_engine_with_fake_fetcher

        captured_out = StringIO()
        with patch("sys.stdout", captured_out):
            exit_code = main(
                [
                    "--db-path",
                    test_db_path,
                    "search",
                    "run",
                    "--profile-id",
                    prof.id,
                    "--min",
                    "2",
                    "--max",
                    "5",
                ]
            )

        assert exit_code == 0
        output = captured_out.getvalue()
        assert "Discovery Session Metrics" in output
        assert "DevOps Role at Target Technologies" in output
        assert "https://boards.greenhouse.io/target/jobs/1" in output
