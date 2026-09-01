import os
import time
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, List
from app.config import settings
from app.services.cta_service import CTAService
from worker.browser_context import BrowserContextManager

logger = logging.getLogger("email_automation.playwright_engine")

@dataclass
class PlaywrightResult:
    success: bool
    final_url: str
    http_status: int
    page_title: str
    screenshot_path: Optional[str]
    execution_time_ms: int
    status_text: str

class PlaywrightEngine:
    @staticmethod
    async def execute_cta_visit(
        target_url: str,
        email_id: int,
        allowed_domains: List[str] = None
    ) -> PlaywrightResult:
        if allowed_domains is None:
            allowed_domains = settings.ALLOWED_CTA_DOMAINS

        # 1. Pre-navigation validation
        if not CTAService.is_domain_allowed(target_url, allowed_domains):
            return PlaywrightResult(
                success=False,
                final_url=target_url,
                http_status=403,
                page_title="Domain Blocked",
                screenshot_path=None,
                execution_time_ms=0,
                status_text="CTA_BLOCKED"
            )

        start_time = time.time()
        os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = os.path.join(settings.SCREENSHOT_DIR, f"email_{email_id}_{int(start_time)}.png")

        blocked_by_redirect = False

        async with BrowserContextManager() as b_mgr:
            context, page = await b_mgr.create_isolated_context()

            # 2. Redirect Validation Listener
            def on_response(response):
                nonlocal blocked_by_redirect
                resp_url = response.url
                if response.status in [301, 302, 303, 307, 308]:
                    location = response.headers.get("location")
                    if location and not CTAService.is_domain_allowed(location, allowed_domains):
                        logger.warning(f"Blocked redirect to un-whitelisted domain: {location}")
                        blocked_by_redirect = True

            page.on("response", on_response)

            try:
                logger.info(f"Playwright navigating to CTA URL: {target_url}")
                response = await page.goto(target_url, wait_until="load", timeout=settings.PLAYWRIGHT_TIMEOUT)

                if blocked_by_redirect:
                    await context.close()
                    return PlaywrightResult(
                        success=False,
                        final_url=page.url,
                        http_status=403,
                        page_title="Redirect Blocked",
                        screenshot_path=None,
                        execution_time_ms=int((time.time() - start_time) * 1000),
                        status_text="CTA_BLOCKED_REDIRECT"
                    )

                http_status = response.status if response else 200
                final_url = page.url
                page_title = await page.title()

                # Post-navigation redirect validation on final URL
                if not CTAService.is_domain_allowed(final_url, allowed_domains):
                    await context.close()
                    return PlaywrightResult(
                        success=False,
                        final_url=final_url,
                        http_status=403,
                        page_title="Final URL Blocked",
                        screenshot_path=None,
                        execution_time_ms=int((time.time() - start_time) * 1000),
                        status_text="CTA_BLOCKED_REDIRECT"
                    )

                # Capture Screenshot
                captured_path = None
                if settings.SCREENSHOT_ON_SUCCESS or (http_status >= 400 and settings.SCREENSHOT_ON_FAILURE):
                    await page.screenshot(path=screenshot_path, full_page=True)
                    captured_path = screenshot_path

                exec_time = int((time.time() - start_time) * 1000)
                await context.close()

                return PlaywrightResult(
                    success=http_status < 400,
                    final_url=final_url,
                    http_status=http_status,
                    page_title=page_title,
                    screenshot_path=captured_path,
                    execution_time_ms=exec_time,
                    status_text="CTA_CLICKED" if http_status < 400 else "CTA_ERROR"
                )

            except Exception as e:
                exec_time = int((time.time() - start_time) * 1000)
                logger.error(f"Playwright execution error on {target_url}: {e}")
                try:
                    if settings.SCREENSHOT_ON_FAILURE:
                        await page.screenshot(path=screenshot_path)
                except Exception:
                    pass

                await context.close()
                return PlaywrightResult(
                    success=False,
                    final_url=target_url,
                    http_status=500,
                    page_title="Error",
                    screenshot_path=screenshot_path if os.path.exists(screenshot_path) else None,
                    execution_time_ms=exec_time,
                    status_text=f"CTA_ERROR: {str(e)}"
                )
