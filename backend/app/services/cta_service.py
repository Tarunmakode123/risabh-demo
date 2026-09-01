import re
import logging
from urllib.parse import urlparse
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger("email_automation.cta_service")

class CTAService:
    @staticmethod
    def is_domain_allowed(url: str, allowed_domains: List[str] = None) -> bool:
        """
        Validates URL against strict domain allowlist.
        Uses exact hostname parsing to reject malicious lookalikes (e.g. evil-example.com or test.example.com.evil.com).
        """
        if not url:
            return False

        if allowed_domains is None:
            allowed_domains = settings.ALLOWED_CTA_DOMAINS

        try:
            parsed = urlparse(url)
            
            # Enforce HTTPS unless local dev environment allows HTTP
            if parsed.scheme not in ["http", "https"]:
                logger.warning(f"Rejected non-HTTP/HTTPS URL scheme: {parsed.scheme}")
                return False

            hostname = (parsed.hostname or "").lower().strip()
            if not hostname:
                return False

            for domain in allowed_domains:
                domain_clean = domain.lower().strip()
                # Exact hostname match or exact subdomain match
                if hostname == domain_clean or hostname.endswith("." + domain_clean):
                    return True

            logger.warning(f"URL hostname '{hostname}' not in ALLOWED_CTA_DOMAINS: {allowed_domains}")
            return False
        except Exception as e:
            logger.error(f"Error parsing URL '{url}': {e}")
            return False

    @classmethod
    def extract_and_validate_cta(
        cls,
        html_body: str,
        plain_body: str,
        cta_selector: str = "a.cta-button",
        cta_text: str = "Get Started",
        cta_url_pattern: str = "",
        allowed_domains: List[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Extracts candidate CTA URLs using Priority 1 (Pattern), Priority 2 (Text), Priority 3 (Selector).
        Returns (candidate_url, status)
        """
        if allowed_domains is None:
            allowed_domains = settings.ALLOWED_CTA_DOMAINS

        candidate_urls: List[str] = []

        if html_body:
            soup = BeautifulSoup(html_body, "html.parser")

            # Priority 1: Configured Exact CTA URL or Pattern match
            if cta_url_pattern:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    if re.search(cta_url_pattern, href, re.IGNORECASE):
                        candidate_urls.append(href)

            # Priority 2: Configured CTA Text Match
            if not candidate_urls and cta_text:
                for a_tag in soup.find_all("a", href=True):
                    text = a_tag.get_text().strip()
                    if cta_text.lower() in text.lower():
                        candidate_urls.append(a_tag["href"].strip())

            # Priority 3: Configured CSS Selector Match
            if not candidate_urls and cta_selector:
                try:
                    for a_tag in soup.select(cta_selector):
                        if a_tag.name == "a" and a_tag.get("href"):
                            candidate_urls.append(a_tag["href"].strip())
                except Exception:
                    pass

            # Fallback: All anchor links in HTML body
            if not candidate_urls:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    if href.startswith("http"):
                        candidate_urls.append(href)

        # Fallback to Plain Body regex
        if not candidate_urls and plain_body:
            found = re.findall(r'https?://[^\s<>"]+', plain_body)
            candidate_urls.extend(found)

        if not candidate_urls:
            return None, "CTA_NOT_FOUND"

        # Validate candidate URLs against ALLOWED_CTA_DOMAINS
        for url in candidate_urls:
            if cls.is_domain_allowed(url, allowed_domains):
                return url, "CTA_VALIDATED"

        return None, "CTA_BLOCKED"
