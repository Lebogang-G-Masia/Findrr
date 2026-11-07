"""Job search query construction (Module 4, FR-012)."""

from typing import List, Optional
from urllib.parse import quote_plus


def build_search_query(
    title: str,
    target_locations: Optional[List[str]] = None,
    remote_preference: Optional[str] = None,
    seniority_level: Optional[str] = None,
) -> str:
    """Construct an effective search query for job discovery.

    Combines job title with target locations and employment preferences.
    """
    clean_title = title.strip()
    query_parts: List[str] = [f'"{clean_title}"']

    if seniority_level and seniority_level not in ("ANY", "NONE"):
        query_parts.append(seniority_level.lower())

    loc_tokens: List[str] = []
    if target_locations:
        for loc in target_locations:
            loc_clean = loc.strip()
            if loc_clean:
                loc_tokens.append(f'"{loc_clean}"')

    if remote_preference and remote_preference.upper() in ("REMOTE", "HYBRID"):
        loc_tokens.append(f'"{remote_preference.lower()}"')

    if loc_tokens:
        if len(loc_tokens) == 1:
            query_parts.append(loc_tokens[0])
        else:
            query_parts.append(f"({' OR '.join(loc_tokens)})")

    # Intent keywords to target actual career postings
    query_parts.append("(jobs OR careers OR hiring OR vacancies)")

    return " ".join(query_parts)


def build_google_search_url(query: str, num_results: int = 10) -> str:
    """Format query into a Google Search URL."""
    encoded = quote_plus(query)
    return f"https://www.google.com/search?q={encoded}&num={num_results}"
