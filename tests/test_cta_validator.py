import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.cta_service import CTAService

def test_domain_allowlist_validation():
    allowed = ["test.example.com", "landing.arrowmail.internal"]

    # Valid URLs
    assert CTAService.is_domain_allowed("https://test.example.com/page?id=123", allowed) is True
    assert CTAService.is_domain_allowed("https://sub.test.example.com/landing", allowed) is True
    assert CTAService.is_domain_allowed("https://landing.arrowmail.internal/welcome", allowed) is True

    # Malicious Lookalikes / Un-whitelisted domains
    assert CTAService.is_domain_allowed("https://evil-example.com", allowed) is False
    assert CTAService.is_domain_allowed("https://test.example.com.evil.com", allowed) is False
    assert CTAService.is_domain_allowed("https://evil.com/?redirect=https://test.example.com", allowed) is False
    assert CTAService.is_domain_allowed("ftp://test.example.com/file", allowed) is False
    print("[PASS] test_domain_allowlist_validation passed!")

def test_cta_extraction_priority():
    html_body = """
    <html>
        <body>
            <a href="https://unapproved.com/privacy">Privacy Policy</a>
            <a class="cta-button" href="https://test.example.com/get-started">Get Started</a>
        </body>
    </html>
    """
    url, status = CTAService.extract_and_validate_cta(
        html_body=html_body,
        plain_body="",
        cta_text="Get Started",
        allowed_domains=["test.example.com"]
    )

    assert url == "https://test.example.com/get-started"
    assert status == "CTA_VALIDATED"
    print("[PASS] test_cta_extraction_priority passed!")

def test_unsubscribe_filtering():
    html_body = """
    <html>
        <body>
            <a href="https://test.example.com/unsubscribe">Unsubscribe from emails</a>
            <a href="https://test.example.com/email-preferences">Manage Preferences</a>
            <a href="https://test.example.com/claim-offer">Claim Your Offer</a>
        </body>
    </html>
    """
    url, status = CTAService.extract_and_validate_cta(
        html_body=html_body,
        plain_body="",
        allowed_domains=["test.example.com"]
    )

    assert url == "https://test.example.com/claim-offer"
    assert status == "CTA_VALIDATED"
    print("[PASS] test_unsubscribe_filtering passed!")

if __name__ == "__main__":
    test_domain_allowlist_validation()
    test_cta_extraction_priority()
    test_unsubscribe_filtering()
