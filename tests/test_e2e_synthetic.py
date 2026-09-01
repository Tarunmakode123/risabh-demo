import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import engine, Base, SessionLocal
from app.models import InboxAccount, ProcessedEmail, EmailLink, CTALog, ReplyLog
from app.services.email_parser import EmailParserService
from app.services.deduplication import DeduplicationService
from app.services.cta_service import CTAService
from app.services.workflow_service import WorkflowService

def test_full_synthetic_e2e_pipeline():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("==================================================")
    print(" Running Synthetic End-to-End Pipeline Test")
    print(" ArrowMail / GreenArrow -> Test Inbox Workflow")
    print("==================================================")

    # 1. Setup Test Inbox Account
    acc = InboxAccount(
        email="synthetic_seed@test.example.com",
        imap_host="imap.example.com",
        smtp_host="smtp.example.com",
        username="synthetic_seed@test.example.com",
        encrypted_password="secret_password"
    )
    db.add(acc)
    db.commit()

    # 2. Simulate Synthetic Campaign Email from ArrowMail/GreenArrow
    raw_mime = (
        b"From: ArrowMail Campaign <campaign@greenarrow.internal>\r\n"
        b"To: Synthetic Seed <synthetic_seed@test.example.com>\r\n"
        b"Subject: Exclusive Member Access\r\n"
        b"Message-ID: <synthetic-e2e-msg-001@greenarrow.internal>\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n\r\n"
        b"<html><body><h1>Welcome!</h1><a class=\"cta-button\" href=\"https://test.example.com/onboarding\">Get Started</a></body></html>"
    )

    parsed = EmailParserService.parse_raw_mime(raw_mime, fallback_recipient=acc.email)
    assert parsed.message_id == "synthetic-e2e-msg-001@greenarrow.internal"

    # 3. Deduplication & Campaign Domain Matching
    assert DeduplicationService.is_duplicate(db, acc.id, parsed.message_id) is False
    allowed_senders = ["greenarrow.internal", "example.com"]
    assert DeduplicationService.is_campaign_allowed(parsed.sender, allowed_senders) is True

    correlation_id = str(uuid.uuid4())
    email_rec = ProcessedEmail(
        correlation_id=correlation_id,
        account_id=acc.id,
        message_id=parsed.message_id,
        thread_id=parsed.thread_id,
        sender=parsed.sender,
        recipient=parsed.recipient,
        subject=parsed.subject,
        status="DETECTED"
    )
    db.add(email_rec)
    db.commit()

    # 4. State Machine Transition: PARSED
    assert WorkflowService.transition_state(db, email_rec, "PARSED") is True
    assert email_rec.status == "PARSED"

    # 5. CTA Extraction & Strict Domain Validation
    allowed_cta_domains = ["test.example.com"]
    cta_url, cta_status = CTAService.extract_and_validate_cta(
        html_body=parsed.html_body,
        plain_body=parsed.plain_body,
        cta_text="Get Started",
        allowed_domains=allowed_cta_domains
    )
    assert cta_url == "https://test.example.com/onboarding"
    assert cta_status == "CTA_VALIDATED"

    assert WorkflowService.transition_state(db, email_rec, "CTA_VALIDATED") is True

    # 6. Simulate Playwright CTA Click Execution Logging
    db.add(CTALog(
        email_id=email_rec.id,
        url=cta_url,
        is_approved=True,
        final_url=cta_url,
        http_status=200,
        page_title="Onboarding Welcome Page",
        screenshot_path=None,
        execution_time_ms=450,
        status="CTA_CLICKED"
    ))
    assert WorkflowService.transition_state(db, email_rec, "CTA_CLICKED") is True

    # 7. Simulate Threaded SMTP Auto-Reply Dispatch
    db.add(ReplyLog(
        email_id=email_rec.id,
        in_reply_to=parsed.message_id,
        references_header=parsed.thread_id or parsed.message_id,
        reply_body="Thanks, received it.",
        delay_seconds=5,
        status="SENT"
    ))
    assert WorkflowService.transition_state(db, email_rec, "REPLIED") is True
    assert WorkflowService.transition_state(db, email_rec, "COMPLETED") is True

    # 8. Idempotency Test: Attempting to process exact same Message-ID again
    assert DeduplicationService.is_duplicate(db, acc.id, parsed.message_id) is True

    # Cleanup
    db.delete(email_rec)
    db.delete(acc)
    db.commit()
    db.close()

    print("[PASS] Full Synthetic End-to-End Pipeline test PASSED cleanly!")

if __name__ == "__main__":
    test_full_synthetic_e2e_pipeline()
