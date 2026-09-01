import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.email_parser import EmailParserService

def test_mime_email_parsing():
    raw_mime = (
        b"From: GreenArrow Sender <sender@example.com>\r\n"
        b"To: Test Inbox <recipient@test.example.com>\r\n"
        b"Subject: Special Campaign Offer\r\n"
        b"Message-ID: <msg-uuid-101@example.com>\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n\r\n"
        b"<html><body><p>Hello!</p><a href=\"https://test.example.com/start\">Get Started</a></body></html>"
    )

    parsed = EmailParserService.parse_raw_mime(raw_mime)

    assert parsed.message_id == "msg-uuid-101@example.com"
    assert parsed.sender == "sender@example.com"
    assert parsed.recipient == "recipient@test.example.com"
    assert parsed.subject == "Special Campaign Offer"
    assert len(parsed.links) == 1
    assert parsed.links[0].anchor_text == "Get Started"
    assert parsed.links[0].url == "https://test.example.com/start"
    print("[PASS] test_mime_email_parsing passed!")

if __name__ == "__main__":
    test_mime_email_parsing()
