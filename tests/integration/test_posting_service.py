"""Integration tests for PostingService orchestration (Module 4)."""

import pytest

from findrr.db.connection import get_connection, init_db
from findrr.db.repository import (
    PostingRepository,
    ProfileRepository,
    SearchConfigRepository,
    TitleRepository,
)
from findrr.models.profile import UserProfile
from findrr.models.search_config import (
    RemotePreference,
    SearchConfiguration,
    SeniorityLevel,
)
from findrr.models.title import GeneralizedTitle
from findrr.search.engine import JobDiscoveryEngine
from findrr.services.posting_service import PostingService

MOCK_DISCOVERY_PAGE = """
<html>
<body>
  <a href="https://acme.com/jobs/1">Backend Developer</a>
  <a href="https://beta.com/jobs/2">Python Engineer</a>
</body>
</html>
"""


def fake_fetcher(url: str) -> str:
    if "google.com" in url:
        return MOCK_DISCOVERY_PAGE
    if "jobs/1" in url:
        return """
        <html><body>
          <h1>Backend Developer</h1>
          <div class="company">Acme Cloud</div>
          <div class="location">Johannesburg</div>
          <div class="description">Develop backend microservices with Python, SQL, and Docker.</div>
          <a href="https://jobs.lever.co/acme/apply">Apply Now</a>
        </body></html>
        """
    if "jobs/2" in url:
        return """
        <html><body>
          <h1>Python Engineer</h1>
          <div class="company">Beta Systems</div>
          <div class="location">Remote</div>
          <div class="description">Looking for Python Engineer proficient in Django and AWS.</div>
        </body></html>
        """
    return ""


@pytest.fixture
def service_fixture(tmp_path):
    db_file = tmp_path / "posting_service_test.db"
    conn = get_connection(str(db_file))
    init_db(conn)

    profile_repo = ProfileRepository(conn)
    title_repo = TitleRepository(conn)
    config_repo = SearchConfigRepository(conn)
    posting_repo = PostingRepository(conn)

    engine = JobDiscoveryEngine(page_fetcher=fake_fetcher)
    service = PostingService(
        posting_repo=posting_repo,
        profile_repo=profile_repo,
        title_repo=title_repo,
        config_repo=config_repo,
        discovery_engine=engine,
    )
    return {
        "service": service,
        "profile_repo": profile_repo,
        "title_repo": title_repo,
        "config_repo": config_repo,
        "posting_repo": posting_repo,
    }


def test_discover_for_profile_workflow(service_fixture):
    service = service_fixture["service"]
    profile_repo = service_fixture["profile_repo"]
    title_repo = service_fixture["title_repo"]
    config_repo = service_fixture["config_repo"]
    posting_repo = service_fixture["posting_repo"]

    # 1. Create Profile
    prof = profile_repo.save_profile(
        UserProfile(
            full_name="Alice Walker",
            email="alice@example.com",
            location="Johannesburg",
        )
    )

    # 2. Add Active Title
    title_repo.save_title(
        GeneralizedTitle(
            profile_id=prof.id,
            primary_title="Software Developer",
            rationale="Suitability based on Python experience",
            supporting_skills=["Python", "Docker"],
        )
    )

    # 3. Add Search Config
    config_repo.save_configuration(
        SearchConfiguration(
            profile_id=prof.id,
            target_locations=["Johannesburg"],
            remote_preference=RemotePreference.REMOTE,
            seniority_level=SeniorityLevel.MID,
            min_results_per_title=2,
            max_results_per_title=5,
        )
    )

    # 4. Run Discovery
    result = service.discover_for_profile(prof.id)

    assert result["title"] == "Software Developer"
    postings = result["postings"]
    metrics = result["metrics"]

    assert len(postings) == 2
    assert metrics.unique_postings_retained == 2
    assert posting_repo.count_postings() == 2

    # Check preferred ATS link was resolved for job 1
    p1 = next(p for p in postings if p.company == "Acme Cloud")
    assert p1.direct_apply_url == "https://jobs.lever.co/acme/apply"
    assert "python" in p1.requirements_extracted

    # 5. Run Discovery Again -> All results are detected as existing DB duplicates
    result_second = service.discover_for_profile(prof.id)
    assert len(result_second["postings"]) == 0
    assert result_second["metrics"].duplicates_detected == 2
    assert posting_repo.count_postings() == 2
