"""Destination link resolution and ATS prioritization (Module 4, FR-014)."""

import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known Applicant Tracking Systems (highest priority destinations)
ATS_DOMAINS = [
    "greenhouse.io",
    "boards.greenhouse.io",
    "lever.co",
    "jobs.lever.co",
    "myworkdayjobs.com",
    "workday.com",
    "smartrecruiters.com",
    "jobs.smartrecruiters.com",
    "apply.workable.com",
    "workable.com",
    "bamboohr.com",
    "ashbyhq.com",
    "jobs.ashbyhq.com",
    "recruitee.com",
    "taleo.net",
    "icims.com",
    "jobvite.com",
    "personio.de",
    "personio.com",
    "breezy.hr",
    "pinpointhq.com",
    "rippling.com",
]

# Known aggregator job boards (discovery only, lower priority than direct/ATS)
AGGREGATOR_DOMAINS = [
    "indeed.com",
    "indeed.co.za",
    "pnet.co.za",
    "careers24.com",
    "linkedin.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "simplyhired.com",
]


def classify_url_destination(url: str) -> str:
    """Classify a URL into 'ATS', 'EMPLOYER_DIRECT', or 'AGGREGATOR'."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    for ats in ATS_DOMAINS:
        if hostname == ats or hostname.endswith("." + ats):
            return "ATS"

    for agg in AGGREGATOR_DOMAINS:
        if hostname == agg or hostname.endswith("." + agg):
            return "AGGREGATOR"

    return "EMPLOYER_DIRECT"


def extract_candidate_links_from_html(html_content: str, base_url: str = "") -> List[str]:
    """Extract potential direct application links from job page HTML.

    Inspects buttons and anchor tags with keywords such as 'apply', 'career',
    'company site', or pointing to known ATS platforms.
    """
    candidates: List[str] = []
    if not html_content:
        return candidates

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        apply_keywords = re.compile(
            r"(apply|application|employer site|company website|apply now|careers)",
            re.IGNORECASE,
        )

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            text = anchor.get_text(separator=" ", strip=True)
            aria_label = anchor.get("aria-label", "")
            title_attr = anchor.get("title", "")

            if not href.startswith("http://") and not href.startswith("https://"):
                continue

            destination_type = classify_url_destination(href)
            if destination_type == "ATS":
                candidates.insert(0, href)
                continue

            combined_text = f"{text} {aria_label} {title_attr}".strip()
            if apply_keywords.search(combined_text) and destination_type != "AGGREGATOR":
                candidates.append(href)
    except Exception as err:
        logger.debug("Failed parsing candidate links from HTML: %s", err)

    return candidates


class LinkResolver:
    """Resolves preferred direct application links from discovery URLs and page content."""

    @classmethod
    def resolve_preferred_destination(
        cls,
        discovery_url: str,
        page_html: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Determine preferred application URL and destination type.

        Returns:
            Tuple of (resolved_application_url, destination_type)
            Destination types: 'ATS', 'EMPLOYER_DIRECT', 'AGGREGATOR'
        """
        initial_classification = classify_url_destination(discovery_url)

        # If discovery_url is already an ATS portal, retain directly
        if initial_classification == "ATS":
            return discovery_url, "ATS"

        # Check page HTML for candidate links (prioritizing ATS links above all)
        extracted_links = (
            extract_candidate_links_from_html(page_html, base_url=discovery_url)
            if page_html
            else []
        )
        for link in extracted_links:
            if classify_url_destination(link) == "ATS":
                logger.info("Resolved ATS destination: %s (from %s)", link, discovery_url)
                return link, "ATS"

        # Retain direct employer URL if discovery_url was direct employer
        if initial_classification == "EMPLOYER_DIRECT":
            return discovery_url, "EMPLOYER_DIRECT"

        # For aggregators, check if an employer direct link was extracted from the page
        for link in extracted_links:
            if classify_url_destination(link) == "EMPLOYER_DIRECT":
                logger.info(
                    "Resolved employer direct link: %s (from aggregator %s)",
                    link,
                    discovery_url,
                )
                return link, "EMPLOYER_DIRECT"

        # Fallback to retaining discovery URL
        return discovery_url, initial_classification
