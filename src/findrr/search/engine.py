"""Search execution engine and posting discovery workflow (Module 4)."""

import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
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
    url = url.strip()
    parsed = urlparse(url)

    # Check for Google search redirect paths (both relative and absolute across regional TLDs)
    is_google_host = not parsed.netloc or "google." in parsed.netloc.lower()
    if is_google_host and parsed.path.rstrip("/") == "/url":
        qs = parse_qs(parsed.query)
        target = qs.get("q") or qs.get("url")
        if target and target[0]:
            target_url = target[0].strip()
            if target_url.startswith("http://") or target_url.startswith("https://"):
                return target_url

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
        prompt_hook: Optional[Callable[[str], None]] = None,
    ):
        self.headless = headless
        self.driver_factory = driver_factory or WebDriverFactory.create_driver
        self.page_fetcher = page_fetcher  # Custom hook for testing / offline evaluation
        self.prompt_hook = prompt_hook or self._default_prompt_hook

    @staticmethod
    def _default_prompt_hook(message: str) -> None:
        input(message)

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
            logger.info(
                "WebDriver initialized successfully. Navigating to search URL: %s",
                search_url,
            )
            driver.get(search_url)
            polite_delay()

            # Handle Google consent popup or redirect if encountered
            self._handle_google_consent_if_present(driver)

            # Check if gated by CAPTCHA / bot challenge (D-001)
            if self.is_captcha_or_bot_challenge(driver):
                resolved = self._handle_human_captcha_challenge(driver)
                if not resolved:
                    logger.warning(
                        "Search discovery halted or gated by unresolved CAPTCHA challenge."
                    )

            search_page_source = driver.page_source
            candidate_urls = self._extract_result_links_from_search_page(search_page_source)
            metrics.results_retrieved = len(candidate_urls)
            logger.info("Retrieved %d candidate search result links from page", len(candidate_urls))

            if len(candidate_urls) == 0:
                curr_url = getattr(driver, "current_url", "unknown")
                logger.warning(
                    "0 candidate result links extracted from search page (current URL: %s). "
                    "Dumping debug snapshot to logs/...",
                    curr_url,
                )
                html_snap, png_snap = self._dump_debug_snapshot(driver, search_page_source)
                logger.warning(
                    "Diagnostic snapshot written: HTML=%s, Screenshot=%s",
                    html_snap,
                    png_snap,
                )

            for idx, target_url in enumerate(candidate_urls, 1):
                if len(extracted_postings) >= eff_max:
                    logger.info(
                        "Reached maximum requested postings (%d). Stopping discovery.",
                        eff_max,
                    )
                    break
                try:
                    logger.info(
                        "[%d/%d] Visiting posting destination: %s",
                        idx,
                        len(candidate_urls),
                        target_url,
                    )
                    polite_delay()
                    driver.get(target_url)
                    posting_html = driver.page_source
                    logger.debug("Destination page HTML length: %d chars", len(posting_html))

                    posting = PostingParser.parse_html(
                        html_content=posting_html,
                        source_url=target_url,
                        search_term_id=search_term_id,
                        fallback_title=title,
                    )
                    if not posting:
                        logger.info(
                            "PostingParser could not extract mandatory fields from: %s",
                            target_url,
                        )
                        continue

                    metrics.postings_extracted += 1
                    if posting.content_hash in seen_hashes:
                        metrics.duplicates_detected += 1
                        logger.info(
                            "Skipped duplicate posting: '%s' at '%s' (hash: %s)",
                            posting.title,
                            posting.company,
                            posting.content_hash,
                        )
                        continue

                    seen_hashes.add(posting.content_hash)
                    extracted_postings.append(posting)
                    logger.info(
                        "Successfully extracted and retained posting: '%s' at '%s'",
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

    def is_captcha_or_bot_challenge(self, driver: Any) -> bool:
        """Detect if Google or search provider presented a CAPTCHA or bot verification challenge."""
        if not driver:
            return False
        try:
            current_url = getattr(driver, "current_url", "")
            if "/sorry/index" in current_url:
                return True

            title = getattr(driver, "title", "").lower()
            if any(
                term in title
                for term in ("sorry...", "unusual traffic", "robot", "human verification")
            ):
                return True

            # Check DOM indicators for reCAPTCHA or Google sorry forms
            selectors = [
                "form#captcha-form",
                "div.g-recaptcha",
                "#recaptcha",
                "iframe[src*='recaptcha']",
                "iframe[src*='captcha']",
            ]
            for sel in selectors:
                try:
                    if driver.find_elements("css selector", sel):
                        return True
                except Exception:
                    continue
        except Exception as exc:
            logger.debug("Exception checking CAPTCHA state: %s", exc)
        return False

    def _handle_human_captcha_challenge(self, driver: Any) -> bool:
        """Prompt user in headful mode to manually solve the CAPTCHA in the visible browser."""
        if self.headless:
            logger.warning(
                "CAPTCHA encountered in headless mode; cannot prompt for human completion."
            )
            return False

        current_url = getattr(driver, "current_url", "unknown")
        logger.warning("Google CAPTCHA challenge detected at: %s", current_url)

        sys.stderr.write("\n" + "=" * 76 + "\n")
        sys.stderr.write("                   [HUMAN VERIFICATION REQUIRED]                    \n")
        sys.stderr.write("=" * 76 + "\n")
        sys.stderr.write(
            "Google has detected automated activity and presented a CAPTCHA challenge.\n"
        )
        sys.stderr.write(
            "Per Findrr invariants, the app will never attempt to bypass or automate CAPTCHAs.\n"
        )
        sys.stderr.write(
            "Please complete the verification directly in the open Chrome browser window.\n\n"
        )
        sys.stderr.write(
            "Press [Enter] once completed and search results appear (or Ctrl+C to abort).\n"
        )
        sys.stderr.write("=" * 76 + "\n\n")

        try:
            prompt_msg = (
                "Waiting for you to complete the challenge in Chrome... (Press Enter when done): "
            )
            self.prompt_hook(prompt_msg)
            polite_delay(2.0, 3.0)

            if not self.is_captcha_or_bot_challenge(driver):
                logger.info("CAPTCHA resolved by user. Resuming job discovery...")
                return True
            else:
                logger.warning("Browser still appears to be on a CAPTCHA or verification page.")
                return False
        except (KeyboardInterrupt, EOFError):
            logger.info("Human verification aborted by user.")
            return False

    def _handle_google_consent_if_present(self, driver: Any) -> bool:
        """Detect and accept Google cookie/privacy consent dialogs if encountered."""
        if not driver:
            return False
        logger.debug("Checking for Google consent banner or redirect...")
        try:
            current_url = getattr(driver, "current_url", "")
            if "consent.google" in current_url:
                logger.info("Detected Google consent redirect page: %s", current_url)

            selectors = [
                ("id", "L2AGLb"),
                ("css selector", "button#L2AGLb"),
                ("css selector", "form[action*='consent'] button"),
                (
                    "xpath",
                    "//button[contains(., 'Accept all') or contains(., 'I agree') or "
                    "contains(., 'Tout accepter') or contains(., 'Alle akzeptieren')]",
                ),
            ]
            for by_type, selector_val in selectors:
                try:
                    elements = driver.find_elements(by_type, selector_val)
                    for btn in elements:
                        if btn.is_displayed():
                            logger.info(
                                "Dismissing Google consent modal via selector (%s: %s)...",
                                by_type,
                                selector_val,
                            )
                            btn.click()
                            polite_delay(1.0, 2.0)
                            return True
                except Exception as sel_err:
                    logger.debug(
                        "Consent check with selector (%s: %s) produced: %s",
                        by_type,
                        selector_val,
                        sel_err,
                    )
        except Exception as exc:
            logger.debug("Consent banner check encountered exception: %s", exc)
        return False

    def _dump_debug_snapshot(
        self, driver: Any, html_source: str, log_dir: str = "logs"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Save HTML snapshot and browser screenshot when search yields 0 candidate links."""
        out_dir = Path(log_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "last_search_page.html"
        png_path = out_dir / "last_search_page.png"

        html_saved: Optional[str] = None
        png_saved: Optional[str] = None

        try:
            html_path.write_text(html_source or "", encoding="utf-8")
            html_saved = str(html_path)
            logger.info("Saved search page HTML snapshot to: %s", html_path)
        except Exception as err:
            logger.warning("Failed saving search page HTML snapshot: %s", err)

        if driver and hasattr(driver, "save_screenshot"):
            try:
                driver.save_screenshot(str(png_path))
                png_saved = str(png_path)
                logger.info("Saved search page screenshot to: %s", png_path)
            except Exception as err:
                logger.warning("Failed saving search page screenshot: %s", err)

        return html_saved, png_saved

    def _extract_result_links_from_search_page(self, html_content: str) -> List[str]:
        """Parse search engine result page and extract job posting target URLs."""
        urls: List[str] = []
        if not html_content:
            return urls

        soup = BeautifulSoup(html_content, "html.parser")
        all_anchors = soup.find_all("a", href=True)
        logger.debug("Scanning %d <a> tags on search page for target links", len(all_anchors))

        for anchor in all_anchors:
            raw_href = anchor.get("href", "").strip()
            if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            cleaned = clean_search_result_url(raw_href)
            if not cleaned:
                continue

            # Skip search engine navigation and internal pages
            parsed = urlparse(cleaned)
            hostname = (parsed.hostname or "").lower()
            path = parsed.path.lower()

            if any(
                domain in hostname
                for domain in (
                    "bing.",
                    "yahoo.",
                    "duckduckgo.",
                    "youtube.",
                    "wikipedia.",
                    "w3.org",
                    "schema.org",
                )
            ):
                continue

            # Skip Google internal navigation and services
            if "google." in hostname:
                if "careers.google" not in hostname:
                    google_internal_prefixes = (
                        "/search",
                        "/preferences",
                        "/advanced_search",
                        "/webhp",
                        "/intl",
                        "/policies",
                        "/terms",
                        "/about",
                        "/services",
                    )
                    if path in ("", "/") or path.startswith(google_internal_prefixes):
                        continue
                    if any(
                        sub in hostname
                        for sub in (
                            "accounts.",
                            "support.",
                            "policies.",
                            "maps.",
                            "mail.",
                            "news.",
                            "drive.",
                        )
                    ):
                        continue

            if cleaned not in urls:
                urls.append(cleaned)
                logger.debug("Candidate search link discovered: %s", cleaned)

        logger.debug(
            "Extracted %d valid candidate destination URLs out of %d anchors",
            len(urls),
            len(all_anchors),
        )
        return urls
