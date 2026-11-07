"""Selenium WebDriver lifecycle and politeness delay management (Module 4)."""

import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = logging.getLogger(__name__)

DEFAULT_MIN_JITTER_SECONDS = 2.0
DEFAULT_MAX_JITTER_SECONDS = 5.0
DEFAULT_CHROME_PROFILE_DIR = "chrome_profile"


def check_display_server_available() -> bool:
    """Check if an active display server (X11 or Wayland) is available on Linux."""
    return bool(os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"))


def polite_delay(
    min_seconds: float = DEFAULT_MIN_JITTER_SECONDS,
    max_seconds: float = DEFAULT_MAX_JITTER_SECONDS,
) -> float:
    """Inject a randomized politeness delay (NFR-003, Jitter 2.0–5.0s)."""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug("Applying politeness jitter: %.2f seconds", delay)
    time.sleep(delay)
    return delay


class WebDriverFactory:
    """Factory for instantiating Selenium WebDriver with headful execution by default."""

    @staticmethod
    def create_driver(
        headless: bool = False,
        browser: str = "chrome",
        page_load_timeout: int = 30,
        user_data_dir: Optional[str] = None,
    ) -> webdriver.Remote:
        """Create and configure a WebDriver instance.

        Headful mode is enforced by default. If headful is requested on Linux without
        an active display server, an explicit RuntimeError is raised.
        """
        logger.info("Initializing Selenium WebDriver (browser=%s, headless=%s)", browser, headless)

        if not headless and not check_display_server_available():
            raise RuntimeError(
                "Headful execution requested but no display server was detected "
                "(neither DISPLAY nor WAYLAND_DISPLAY is set). "
                "Per system invariants, headful execution is required by default. "
                "Ensure an X11/Wayland display server is running or provide display access."
            )

        driver: webdriver.Remote
        if browser.lower() == "firefox":
            options = FirefoxOptions()
            if headless:
                options.add_argument("-headless")
            driver = webdriver.Firefox(options=options)
        else:
            # Default to Chrome / Chromium
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1280,900")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )

            profile_target = (
                user_data_dir
                if user_data_dir is not None
                else os.getenv("FINDRR_CHROME_PROFILE_DIR", DEFAULT_CHROME_PROFILE_DIR)
            )
            if profile_target:
                try:
                    profile_path = Path(profile_target).resolve()
                    profile_path.mkdir(parents=True, exist_ok=True)
                    options.add_argument(f"--user-data-dir={profile_path}")
                    logger.debug("Configured persistent Chrome profile: %s", profile_path)
                except Exception as err:
                    logger.warning(
                        "Could not configure Chrome profile dir '%s': %s",
                        profile_target,
                        err,
                    )

            driver = webdriver.Chrome(options=options)

        driver.set_page_load_timeout(page_load_timeout)
        return driver
