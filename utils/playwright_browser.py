from __future__ import annotations

from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from utils.config_manager import ConfigManager
from utils.logger import AppLogger
from utils.retry_utils import retry


class PlaywrightBrowser:
    """A thin abstraction for launching Playwright browsers locally."""

    def __init__(self, config_manager: ConfigManager | None = None, logger: AppLogger | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.logger = (logger or AppLogger(self.config_manager)).get_logger()
        self.headless = bool(self.config_manager.get("browser.headless", True))
        self.timeout = int(self.config_manager.get("browser.timeout", 30000))
        self.retries = int(self.config_manager.get("browser.retries", 3))
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def __enter__(self) -> "PlaywrightBrowser":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def start(self) -> None:
        """Launch a Playwright browser instance."""

        if self._browser is not None:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)

    def close(self) -> None:
        """Close the browser and stop Playwright."""

        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    @retry(max_attempts=3, delay_seconds=0.2)
    def open_page(self, url: str) -> Page:
        """Open a page and return it."""

        self.start()
        page = self._browser.new_page() if self._browser is not None else None
        if page is None:
            raise RuntimeError("Playwright browser not initialized")
        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
        return page
