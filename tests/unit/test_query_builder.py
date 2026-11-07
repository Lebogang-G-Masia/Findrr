"""Unit tests for search query builder (Module 4, FR-012)."""

from findrr.search.query_builder import build_google_search_url, build_search_query


def test_build_search_query_simple():
    query = build_search_query("Software Developer")
    assert '"Software Developer"' in query
    assert "(jobs OR careers OR hiring OR vacancies)" in query


def test_build_search_query_with_locations():
    query = build_search_query("Data Engineer", target_locations=["Johannesburg", "Pretoria"])
    assert '"Data Engineer"' in query
    assert '("Johannesburg" OR "Pretoria")' in query


def test_build_search_query_with_remote_and_seniority():
    query = build_search_query(
        "DevOps Engineer",
        target_locations=["Cape Town"],
        remote_preference="REMOTE",
        seniority_level="SENIOR",
    )
    assert '"DevOps Engineer"' in query
    assert "senior" in query
    assert '"cape town"' in query or '"Cape Town"' in query
    assert '"remote"' in query


def test_build_google_search_url():
    url = build_google_search_url('"Backend Developer" Johannesburg', num_results=10)
    assert url.startswith("https://www.google.com/search?q=")
    assert "Backend+Developer" in url or "Backend%20Developer" in url or "Backend" in url
    assert "num=10" in url
