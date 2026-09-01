import logging
import random
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import httpx
from app.config import settings

logger = logging.getLogger("warmup.html_processor")

class HTMLProcessorService:
    def __init__(self, user_agent: str = settings.USER_AGENT):
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def load_tracking_pixels(self, html_content: str) -> int:
        """Finds image URLs / tracking pixels in the HTML and sends GET requests to trigger open tracking."""
        if not html_content:
            return 0

        soup = BeautifulSoup(html_content, "html.parser")
        images = soup.find_all("img")
        pixel_count = 0

        async with httpx.AsyncClient(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
            for img in images:
                src = img.get("src")
                if not src:
                    continue

                parsed = urlparse(src)
                if parsed.scheme in ["http", "https"]:
                    try:
                        resp = await client.get(src)
                        pixel_count += 1
                        logger.debug(f"Loaded image/pixel: {src} -> Status {resp.status_code}")
                    except Exception as e:
                        logger.debug(f"Failed to load image/pixel {src}: {e}")

        return pixel_count

    def extract_cta_links(self, html_content: str) -> list[str]:
        """Extracts valid Call-To-Action (CTA) hyperlinks from HTML email body."""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        anchor_tags = soup.find_all("a")
        valid_links = []

        ignore_keywords = [
            "unsubscribe", "opt-out", "optout", "privacy", "terms", "manage-preferences", 
            "preferences", "facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com"
        ]

        for tag in anchor_tags:
            href = tag.get("href")
            link_text = tag.get_text().strip().lower()
            
            if not href:
                continue

            href_lower = href.lower()
            parsed = urlparse(href)

            # Skip non-http schemes like mailto:, tel:, javascript:
            if parsed.scheme not in ["http", "https"]:
                continue

            # Skip unsubscribe / social media / footer links
            should_ignore = False
            for kw in ignore_keywords:
                if kw in href_lower or kw in link_text:
                    should_ignore = True
                    break

            if not should_ignore:
                valid_links.append(href)

        return list(set(valid_links))

    async def click_cta_link(self, links: list[str]) -> tuple[bool, str, str]:
        """Randomly selects a valid CTA link and executes an HTTP GET request to simulate a click."""
        if not links:
            return False, "", "No CTA links found in email body"

        target_url = random.choice(links)
        logger.info(f"Simulating CTA click on URL: {target_url}")

        async with httpx.AsyncClient(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(target_url)
                if response.status_code < 400:
                    return True, target_url, f"Successfully clicked CTA (HTTP {response.status_code})"
                else:
                    return False, target_url, f"Clicked CTA returned status code HTTP {response.status_code}"
            except Exception as e:
                logger.error(f"Error clicking CTA URL {target_url}: {e}")
                return False, target_url, f"CTA Click Error: {str(e)}"
