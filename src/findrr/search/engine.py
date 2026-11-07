"""Search execution engine and posting discovery workflow (Module 4)."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from findrr.models.posting import DiscoveryMetrics, JobPostingCreate
from findrr.search.driver import WebDriverFactory, polite_delay
from findrr.search.posting_parser import PostingParser
from findrr.search.query_builder import build_google_search_url, build_search_query

logger = logging.getLogger(__name__)


def clean_search_result_url(url: str) -> Optional[str]:
    """Extract destination URL from search engine redirect links (e.g., /url?q=...)."""
    if not url:
        return None
    parsed = urlparse(url)
    if "google.com" in parsed.netloc and parsed.path == "/url":
        qs = parse_qs(parsed.query)
        target = qs.get("q")
        if target:
            return target[0]
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return None


class IJobDiscoveryEngine(ABC):
    """Abstract interface for job discovery engines (NFR-010)."""

    @abstractmethod
    def discover(
        self,
        title: str,
        target_locations: Optional[List[str]] = None,
        remote_preference: Optional[str] = None,
        seniority_level: Optional[str] = None,
        search_term_id: Optional[str] = None,
        min_results: int = 2,
        max_results: int = 10,
    ) -> Tuple[List[JobPostingCreate], DiscoveryMetrics]:
        """Execute discovery workflow for a single job title."""
        pass


class JobDiscoveryEngine(IJobDiscoveryEngine):
    """Headful Selenium-based job discovery engine."""

    def __init__(
        self,
        headless: bool = False,
        driver_factory: Optional[Callable[..., Any]] = None,
        page_fetcher: Optional[Callable[[str], str]] = None,
    ):
        self.headless = headless
        self.driver_factory = driver_factory or WebDriverFactory.create_driver
        self.page_fetcher = page_fetcher  # Custom hook for testing / offline evaluation

    def discover(
        self,
        title: str,
        target_locations: Optional[List[str]] = None,
        remote_preference: Optional[str] = None,
        seniority_level: Optional[str] = None,
        search_term_id: Optional[str] = None,
        min_results: int = 2,
        max_results: int = 10,
    ) -> Tuple[List[JobPostingCreate], DiscoveryMetrics]:
        """Execute search query and extract between min_results and max_results postings.

        Bounds: 2 to 10 postings per title (FR-013).
        Never fabricates if fewer than min_results are found (FR-017).
        """
        # Validate limits against Module 4 invariant: bounds must be [2, 10]
        eff_min = max(2, min_results)
        eff_max = min(10, max_results)
        if eff_min > eff_max:
            eff_min = eff_max

        query = build_search_query(
            title=title,
            target_locations=target_locations,
            remote_preference=remote_preference,
            seniority_level=seniority_level,
        )
        search_url = build_google_search_url(query, num_results=eff_max * 2)

        metrics = DiscoveryMetrics(query=query)
        extracted_postings: List[JobPostingCreate] = []
        seen_hashes = set()

        logger.info(
            "Executing job discovery for title '%s' (bounds: [%d, %d])",
            title,
            eff_min,
            eff_max,
        )

        # Testing hook: if page_fetcher is provided, use it directly without spinning up Selenium
        if self.page_fetcher:
            search_page_html = self.page_fetcher(search_url)
            candidate_urls = self._extract_result_links_from_search_page(search_page_html)
            metrics.results_retrieved = len(candidate_urls)

            for target_url in candidate_urls:
                if len(extracted_postings) >= eff_max:
                    break
                try:
                    posting_html = self.page_fetcher(target_url)
                    posting = PostingParser.parse_html(
                        html_content=posting_html,
                        source_url=target_url,
                        search_term_id=search_term_id,
                        fallback_title=title,
                    )
                    if posting:
                        metrics.postings_extracted += 1
                        if posting.content_hash in seen_hashes:
                            metrics.duplicates_detected += 1
                            continue
                        seen_hashes.add(posting.content_hash)
                        extracted_postings.append(posting)
                except Exception as err:
                    logger.warning("Error fetching candidate posting %s: %s", target_url, err)

            metrics.unique_postings_retained = len(extracted_postings)
            return extracted_postings, metrics

        # Live Selenium Execution (Headful by default)
        driver = None
        try:
            driver = self.driver_factory(headless=self.headless)
            logger.info("Navigating to search URL: %s", search_url)
            driver.get(search_url)
            polite_delay()

            search_page_source = driver.page_source
            candidate_urls = self._extract_result_links_from_search_page(search_page_source)
            metrics.results_retrieved = len(candidate_urls)
            logger.info("Retrieved %d search result links", len(candidate_urls))

            for target_url in candidate_urls:
                if len(extracted_postings) >= eff_max:
                    break
                try:
                    logger.info("Visiting posting destination: %s", target_url)
                    polite_delay()
                    driver.get(target_url)
                    posting_html = driver.page_source

                    posting = PostingParser.parse_html(
                        html_content=posting_html,
                        source_url=target_url,
                        search_term_id=search_term_id,
                        fallback_title=title,
                    )
                    if posting:
                        metrics.postings_extracted += 1
                        if posting.content_hash in seen_hashes:
                            metrics.duplicates_detected += 1
                            logger.info(
                                "Skipped duplicate posting: %s at %s",
                                posting.title,
                                posting.company,
                            )
                            continue
                        seen_hashes.add(posting.content_hash)
                        extracted_postings.append(posting)
                        logger.info(
                            "Extracted valid posting: '%s' at '%s'",
                            posting.title,
                            posting.company,
                        )
                except Exception as err:
                    logger.warning("Failed processing candidate posting %s: %s", target_url, err)
                    continue

        except Exception as err:
            logger.error("Job discovery session failed: %s", err)
            raise
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        metrics.unique_postings_retained = len(extracted_postings)
        logger.info(
            "Discovery complete: %d retrieved, %d extracted, %d retained unique",
            metrics.results_retrieved,
            metrics.postings_extracted,
            metrics.unique_postings_retained,
        )
        return extracted_postings, metrics

    def _extract_result_links_from_search_page(self, html_content: str) -> List[str]:
        """Parse search engine result page and extract job posting target URLs."""
        urls: List[str] = []
        if not html_content:
            return urls

        soup = BeautifulSoup(html_content, "html.parser")
        for anchor in soup.find_all("a", href=True):
            raw_href = anchor.get("href", "")
            cleaned = clean_search_result_url(raw_href)
            if not cleaned:
                continue

            # Skip search engine navigation and internal pages
            parsed = urlparse(cleaned)
            hostname = (parsed.hostname or "").lower()
            if any(
                domain in hostname
                for domain in (
                    "google.",
                    "bing.",
                    "yahoo.",
                    "duckduckgo.",
                    "youtube.",
                    "wikipedia.",
                )
            ):
                continue

            if cleaned not in urls:
                urls.append(cleaned)

        return urls
