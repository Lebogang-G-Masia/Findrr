"""Unit tests for search logging, URL cleaning, link extraction, and snapshot dumping."""

import logging
from pathlib import Path
from unittest.mock import MagicMock

from findrr.cli.main import build_parser, configure_logging
from findrr.search.engine import JobDiscoveryEngine, clean_search_result_url
from findrr.search.posting_parser import PostingParser


def test_clean_search_result_url_relative_google():
    """Verify that relative Google redirect URLs (/url?q=...) are correctly unpacked."""
    rel_url = "/url?q=https://careers.acme.com/jobs/123&sa=U&ved=2ahUKEwj"
    assert clean_search_result_url(rel_url) == "https://careers.acme.com/jobs/123"

    rel_url_param = "/url?url=https://techcorp.org/positions/456&source=google"
    assert clean_search_result_url(rel_url_param) == "https://techcorp.org/positions/456"


def test_clean_search_result_url_regional_google():
    """Verify regional Google redirect domains (google.co.za, google.co.uk) are extracted."""
    za_url = "https://www.google.co.za/url?q=https://capetown.io/lead-dev&sa=U"
    assert clean_search_result_url(za_url) == "https://capetown.io/lead-dev"

    uk_url = "https://www.google.co.uk/url?q=https://londondevs.co.uk/engineer"
    assert clean_search_result_url(uk_url) == "https://londondevs.co.uk/engineer"


def test_clean_search_result_url_direct_urls():
    """Verify direct HTTP/HTTPS URLs are passed through as-is."""
    direct = "https://boards.greenhouse.io/acmecorp/jobs/999"
    assert clean_search_result_url(direct) == direct

    # Non-HTTP relative URLs without /url?q should return None
    assert clean_search_result_url("/preferences") is None
    assert clean_search_result_url("") is None
    assert clean_search_result_url("javascript:void(0)") is None


def test_extract_result_links_from_search_page_with_relative_links():
    """Verify link extraction from Google SERP with relative /url?q= links."""
    engine = JobDiscoveryEngine()
    serp_html = """
    <html>
    <body>
      <div id="search">
        <a href="/url?q=https://company-a.com/job/1&sa=U">Job A</a>
        <a href="/url?q=https://company-b.com/job/2&sa=U">Job B</a>
        <a href="https://www.google.co.za/preferences">Preferences</a>
        <a href="https://support.google.com/websearch">Support</a>
        <a href="/url?q=https://company-a.com/job/1&sa=U">Duplicate Job A</a>
      </div>
    </body>
    </html>
    """
    links = engine._extract_result_links_from_search_page(serp_html)
    assert links == [
        "https://company-a.com/job/1",
        "https://company-b.com/job/2",
    ]


def test_handle_google_consent_if_present():
    """Verify _handle_google_consent_if_present clicks matching consent button when displayed."""
    engine = JobDiscoveryEngine()

    mock_driver = MagicMock()
    mock_btn = MagicMock()
    mock_btn.is_displayed.return_value = True

    def find_mock_elements(by: str, sel: str):
        return [mock_btn] if sel == "button#L2AGLb" else []

    mock_driver.find_elements.side_effect = find_mock_elements

    handled = engine._handle_google_consent_if_present(mock_driver)
    assert handled is True
    mock_btn.click.assert_called_once()


def test_handle_google_consent_not_present():
    """Verify _handle_google_consent_if_present returns False cleanly when no modal exists."""
    engine = JobDiscoveryEngine()
    mock_driver = MagicMock()
    mock_driver.find_elements.return_value = []

    handled = engine._handle_google_consent_if_present(mock_driver)
    assert handled is False


def test_dump_debug_snapshot(tmp_path: Path):
    """Verify _dump_debug_snapshot outputs HTML and screenshot files."""
    engine = JobDiscoveryEngine()
    mock_driver = MagicMock()

    html_content = "<html><body><h1>Google Results</h1></body></html>"
    log_dir = str(tmp_path / "test_logs")

    html_path, png_path = engine._dump_debug_snapshot(mock_driver, html_content, log_dir=log_dir)

    assert html_path is not None
    assert Path(html_path).exists()
    assert Path(html_path).read_text(encoding="utf-8") == html_content

    assert png_path is not None
    mock_driver.save_screenshot.assert_called_once_with(png_path)


def test_posting_parser_extracts_company_from_meta():
    """Verify PostingParser falls back to og:site_name and author meta tags for company."""
    html = """
    <html>
      <head>
        <meta property="og:site_name" content="Acme Cloud Innovations" />
      </head>
      <body>
        <h1>Lead Infrastructure Engineer</h1>
        <div class="description">
          We are seeking a senior cloud architect to build multi-region AWS services.
        </div>
      </body>
    </html>
    """
    posting = PostingParser.parse_html(html, source_url="https://acme.org/careers/lead")
    assert posting is not None
    assert posting.company == "Acme Cloud Innovations"
    assert posting.title == "Lead Infrastructure Engineer"


def test_configure_logging(tmp_path: Path):
    """Verify configure_logging sets up both console and file handlers without crashing."""
    log_file = tmp_path / "findrr_test.log"
    configure_logging(verbose=True, log_file=str(log_file))

    logger = logging.getLogger("test_logger")
    logger.debug("Debug message from unit test")
    logger.info("Info message from unit test")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Debug message from unit test" in content
    assert "Info message from unit test" in content


def test_search_run_parser_accepts_limit_alias():
    """Verify that findrr search run accepts --limit as an alias for --max."""
    parser = build_parser()
    parsed = parser.parse_args(["search", "run", "--limit", "5"])
    assert parsed.max == 5


def test_is_captcha_or_bot_challenge_detection():
    """Verify detection of Google sorry/index redirect and CAPTCHA DOM markers."""
    engine = JobDiscoveryEngine()

    # URL match
    mock_driver_url = MagicMock()
    mock_driver_url.current_url = "https://www.google.com/sorry/index?continue=..."
    assert engine.is_captcha_or_bot_challenge(mock_driver_url) is True

    # Title match
    mock_driver_title = MagicMock()
    mock_driver_title.current_url = "https://www.google.com/search?q=test"
    mock_driver_title.title = "Sorry... We have detected unusual traffic from your computer network"
    assert engine.is_captcha_or_bot_challenge(mock_driver_title) is True

    # Clean normal page
    mock_clean = MagicMock()
    mock_clean.current_url = "https://www.google.com/search?q=test"
    mock_clean.title = "Software Engineer - Google Search"
    mock_clean.find_elements.return_value = []
    assert engine.is_captcha_or_bot_challenge(mock_clean) is False


def test_handle_human_captcha_challenge_resolved():
    """Verify human-in-the-loop prompt flow when user solves challenge."""
    prompt_called = []

    def fake_prompt(msg: str):
        prompt_called.append(msg)

    engine = JobDiscoveryEngine(headless=False, prompt_hook=fake_prompt)

    mock_driver = MagicMock()
    # Initially on sorry/index, but after prompt returns clean search page
    mock_driver.current_url = "https://www.google.com/sorry/index"
    mock_driver.title = "Sorry..."

    def simulate_user_solving(msg: str):
        prompt_called.append(msg)
        mock_driver.current_url = "https://www.google.com/search?q=test"
        mock_driver.title = "Results"
        mock_driver.find_elements.return_value = []

    engine.prompt_hook = simulate_user_solving

    resolved = engine._handle_human_captcha_challenge(mock_driver)
    assert resolved is True
    assert len(prompt_called) == 1


def test_handle_human_captcha_challenge_headless():
    """Verify headless mode refuses to prompt and cleanly returns False."""
    prompt_called = []
    engine = JobDiscoveryEngine(
        headless=True,
        prompt_hook=lambda msg: prompt_called.append(msg),
    )
    mock_driver = MagicMock()
    mock_driver.current_url = "https://www.google.com/sorry/index"

    resolved = engine._handle_human_captcha_challenge(mock_driver)
    assert resolved is False
    assert len(prompt_called) == 0
