import re
import logging
from urllib.parse import urlparse
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger("email_automation.cta_service")

UNSUBSCRIBE_KEYWORDS = [
    "unsubscribe", "optout", "opt-out", "opt_out", "remove-me", "remove", 
    "email-preferences", "email_preferences", "manage-preferences", 
    "subscription-preferences", "unsub"
]

class CTAService:
    @staticmethod
    def is_unsubscribe_link(url: str, anchor_text: str = "") -> bool:
        """
        Detects if a URL or anchor text represents an Unsubscribe, Opt-Out, or Email Preference link.
        """
        combined = f"{url} {anchor_text}".lower().strip()
        for kw in UNSUBSCRIBE_KEYWORDS:
            if kw in combined:
                return True
        return False

    @classmethod
    def is_domain_allowed(cls, url: str, allowed_domains: List[str] = None, anchor_text: str = "") -> bool:
        """
        Validates URL against strict domain allowlist and ensures it is NOT an unsubscribe link.
        """
        if not url:
            return False

        # Reject unsubscribe links immediately
        if cls.is_unsubscribe_link(url, anchor_text):
            logger.info(f"Skipping unsubscribe / opt-out link: '{url}' (Anchor: '{anchor_text}')")
            return False

        if allowed_domains is None:
            allowed_domains = settings.ALLOWED_CTA_DOMAINS

        if isinstance(allowed_domains, str):
            allowed_domains = [d.strip() for d in allowed_domains.split(",") if d.strip()]

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
        Filters out unsubscribe/opt-out links.
        Returns (candidate_url, status)
        """
        if allowed_domains is None:
            allowed_domains = settings.ALLOWED_CTA_DOMAINS

        candidate_items: List[Tuple[str, str]] = []  # (url, anchor_text)

        if html_body:
            soup = BeautifulSoup(html_body, "html.parser")

            # Priority 1: Configured Exact CTA URL or Pattern match
            if cta_url_pattern:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    anchor = a_tag.get_text().strip()
                    if re.search(cta_url_pattern, href, re.IGNORECASE):
                        if not cls.is_unsubscribe_link(href, anchor):
                            candidate_items.append((href, anchor))

            # Priority 2: Configured CTA Text Match
            if not candidate_items and cta_text:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    anchor = a_tag.get_text().strip()
                    if cta_text.lower() in anchor.lower():
                        if not cls.is_unsubscribe_link(href, anchor):
                            candidate_items.append((href, anchor))

            # Priority 3: Configured CSS Selector Match
            if not candidate_items and cta_selector:
                try:
                    for a_tag in soup.select(cta_selector):
                        if a_tag.name == "a" and a_tag.get("href"):
                            href = a_tag["href"].strip()
                            anchor = a_tag.get_text().strip()
                            if not cls.is_unsubscribe_link(href, anchor):
                                candidate_items.append((href, anchor))
                except Exception:
                    pass

            # Fallback: All anchor links in HTML body (skipping unsubscribe links)
            if not candidate_items:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    anchor = a_tag.get_text().strip()
                    if href.startswith("http") and not cls.is_unsubscribe_link(href, anchor):
                        candidate_items.append((href, anchor))

        # Fallback to Plain Body regex
        if not candidate_items and plain_body:
            found = re.findall(r'https?://[^\s<>"]+', plain_body)
            for url in found:
                if not cls.is_unsubscribe_link(url, ""):
                    candidate_items.append((url, ""))

        if not candidate_items:
            return None, "CTA_NOT_FOUND"

        # Validate candidate URLs against ALLOWED_CTA_DOMAINS
        for url, anchor in candidate_items:
            if cls.is_domain_allowed(url, allowed_domains, anchor_text=anchor):
                return url, "CTA_VALIDATED"

        return None, "CTA_BLOCKED"
