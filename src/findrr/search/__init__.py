"""Web search automation and posting discovery subsystem (Module 4)."""

from findrr.search.driver import (
    WebDriverFactory,
    check_display_server_available,
    polite_delay,
)
from findrr.search.engine import (
    IJobDiscoveryEngine,
    JobDiscoveryEngine,
    clean_search_result_url,
)
from findrr.search.link_resolver import (
    LinkResolver,
    classify_url_destination,
    extract_candidate_links_from_html,
)
from findrr.search.posting_parser import (
    PostingParser,
    compute_content_hash,
    detect_availability,
    extract_skills_keywords,
)
from findrr.search.query_builder import (
    build_google_search_url,
    build_search_query,
)

__all__ = [
    "WebDriverFactory",
    "check_display_server_available",
    "polite_delay",
    "IJobDiscoveryEngine",
    "JobDiscoveryEngine",
    "clean_search_result_url",
    "LinkResolver",
    "classify_url_destination",
    "extract_candidate_links_from_html",
    "PostingParser",
    "compute_content_hash",
    "detect_availability",
    "extract_skills_keywords",
    "build_search_query",
    "build_google_search_url",
]
