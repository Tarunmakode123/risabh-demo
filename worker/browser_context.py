import os
import logging
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings

logger = logging.getLogger("email_automation.playwright_context")

class BrowserContextManager:
    def __init__(self, headless: bool = settings.PLAYWRIGHT_HEADLESS, timeout: int = settings.PLAYWRIGHT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser: Optional[Browser] = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        return self

    async def create_isolated_context(self) -> Tuple[BrowserContext, Page]:
        if not self._browser:
            raise RuntimeError("Browser engine not initialized")

        context = await self._browser.new_context(
            user_agent=settings.USER_AGENT,
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True
        )
        context.set_default_timeout(self.timeout)
        page = await context.new_page()
        return context, page

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
