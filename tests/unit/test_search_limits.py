"""Unit tests for search result limits [2, 10] and zero-fabrication invariant (FR-013, FR-017)."""

from findrr.search.engine import JobDiscoveryEngine

MOCK_SEARCH_PAGE_MULTIPLE = """
<html>
<body>
  <a href="https://acme.com/jobs/1">Acme Job 1</a>
  <a href="https://beta.com/jobs/2">Beta Job 2</a>
  <a href="https://gamma.com/jobs/3">Gamma Job 3</a>
  <a href="https://delta.com/jobs/4">Delta Job 4</a>
</body>
</html>
"""

MOCK_SEARCH_PAGE_SINGLE = """
<html>
<body>
  <a href="https://acme.com/jobs/1">Sole Acme Job</a>
</body>
</html>
"""

MOCK_SEARCH_PAGE_EMPTY = """
<html>
<body>
  <p>No results found for your query.</p>
</body>
</html>
"""


def fake_page_fetcher_multiple(url: str) -> str:
    if "google.com" in url:
        return MOCK_SEARCH_PAGE_MULTIPLE
    if "jobs/1" in url:
        return "<html><body><h1>Job 1</h1><div class='company'>Acme</div></body></html>"
    if "jobs/2" in url:
        return "<html><body><h1>Job 2</h1><div class='company'>Beta</div></body></html>"
    if "jobs/3" in url:
        return "<html><body><h1>Job 3</h1><div class='company'>Gamma</div></body></html>"
    if "jobs/4" in url:
        return "<html><body><h1>Job 4</h1><div class='company'>Delta</div></body></html>"
    return ""


def fake_page_fetcher_single(url: str) -> str:
    if "google.com" in url:
        return MOCK_SEARCH_PAGE_SINGLE
    if "jobs/1" in url:
        return (
            "<html><body><h1>Lone Engineer</h1><div class='company'>Acme Corp</div>"
            "<div class='description'>Only one posting available here.</div></body></html>"
        )
    return ""


def fake_page_fetcher_empty(url: str) -> str:
    return MOCK_SEARCH_PAGE_EMPTY


def fake_page_fetcher_duplicates(url: str) -> str:
    if "google.com" in url:
        return MOCK_SEARCH_PAGE_MULTIPLE
    # Both URLs return identical job text -> same content hash
    return (
        "<html><body><h1>Software Engineer</h1><div class='company'>Acme</div>"
        "<div class='description'>Identical description for duplicate testing.</div></body></html>"
    )


def test_search_limits_enforced_upper_bound():
    engine = JobDiscoveryEngine(page_fetcher=fake_page_fetcher_multiple)
    # Request max 3 (within [2, 10])
    postings, metrics = engine.discover("Software Engineer", min_results=2, max_results=3)
    assert len(postings) == 3
    assert metrics.unique_postings_retained == 3


def test_search_limits_clamped_to_canonical_range():
    engine = JobDiscoveryEngine(page_fetcher=fake_page_fetcher_multiple)
    # Request max 15 (should clamp to max 10)
    postings, metrics = engine.discover("Software Engineer", min_results=1, max_results=15)
    # We only have 4 mock jobs
    assert len(postings) == 4
    assert metrics.unique_postings_retained == 4


def test_zero_fabrication_when_fewer_than_minimum():
    engine = JobDiscoveryEngine(page_fetcher=fake_page_fetcher_single)
    # Request min 2, but only 1 exists
    postings, metrics = engine.discover("Rare Specialist", min_results=2, max_results=10)
    # Must retain exactly 1 result, NEVER fabricating synthetic entries (FR-017)
    assert len(postings) == 1
    assert metrics.results_retrieved == 1
    assert metrics.unique_postings_retained == 1
    assert postings[0].company == "Acme Corp"


def test_zero_fabrication_when_zero_results():
    engine = JobDiscoveryEngine(page_fetcher=fake_page_fetcher_empty)
    postings, metrics = engine.discover("Nonexistent Job Title", min_results=2, max_results=10)
    assert len(postings) == 0
    assert metrics.results_retrieved == 0
    assert metrics.unique_postings_retained == 0


def test_duplicate_rejection_via_content_hash():
    engine = JobDiscoveryEngine(page_fetcher=fake_page_fetcher_duplicates)
    postings, metrics = engine.discover("Software Engineer", min_results=2, max_results=5)
    # Only 1 unique posting should be retained; subsequent identical postings are dropped
    assert len(postings) == 1
    assert metrics.duplicates_detected >= 1
    assert metrics.unique_postings_retained == 1
