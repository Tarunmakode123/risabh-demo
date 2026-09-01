import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import engine, Base, SessionLocal
from app.models import InboxAccount, ProcessedEmail
from app.services.deduplication import DeduplicationService

def test_deduplication_and_campaign_matching():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create test account
    acc = InboxAccount(
        email="dedup_test@example.com",
        imap_host="imap.example.com",
        smtp_host="smtp.example.com",
        username="dedup_test@example.com",
        encrypted_password="secret"
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)

    # 1. Test Duplicate Detection
    msg_id = "unique-msg-id-123@example.com"
    assert DeduplicationService.is_duplicate(db, acc.id, msg_id) is False

    email_rec = ProcessedEmail(
        account_id=acc.id,
        message_id=msg_id,
        sender="campaign@example.com",
        recipient="inbox@test.example.com",
        status="DETECTED"
    )
    db.add(email_rec)
    db.commit()

    assert DeduplicationService.is_duplicate(db, acc.id, msg_id) is True

    # 2. Test Campaign Sender Domain Matching
    allowed_senders = ["example.com", "greenarrow.internal"]
    assert DeduplicationService.is_campaign_allowed("campaign@example.com", allowed_senders) is True
    assert DeduplicationService.is_campaign_allowed("unauthorized@spammer.org", allowed_senders) is False

    # Cleanup
    db.delete(email_rec)
    db.delete(acc)
    db.commit()
    db.close()
    print("[PASS] test_deduplication_and_campaign_matching passed!")

if __name__ == "__main__":
    test_deduplication_and_campaign_matching()
