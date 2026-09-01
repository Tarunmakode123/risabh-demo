import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import engine, Base, SessionLocal
from app.models import InboxAccount, ProcessedEmail, AuditLog
from app.services.workflow_service import WorkflowService

def test_workflow_state_machine():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    acc = InboxAccount(
        email="wf_unique@example.com",
        imap_host="imap.example.com",
        smtp_host="smtp.example.com",
        username="wf_unique@example.com",
        encrypted_password="secret"
    )
    db.add(acc)
    db.commit()

    email_rec = ProcessedEmail(
        account_id=acc.id,
        message_id="wf-msg-1@example.com",
        sender="sender@example.com",
        recipient="workflow_test@example.com",
        status="DETECTED"
    )
    db.add(email_rec)
    db.commit()

    # Test Valid Transitions
    assert WorkflowService.transition_state(db, email_rec, "PARSED") is True
    assert email_rec.status == "PARSED"
    assert email_rec.opened_at is not None

    assert WorkflowService.transition_state(db, email_rec, "CTA_VALIDATED") is True
    assert WorkflowService.transition_state(db, email_rec, "CTA_CLICKED") is True
    assert WorkflowService.transition_state(db, email_rec, "REPLY_QUEUED") is True
    assert WorkflowService.transition_state(db, email_rec, "REPLIED") is True
    assert WorkflowService.transition_state(db, email_rec, "COMPLETED") is True

    # Audit Logs Created
    audit_count = db.query(AuditLog).filter(AuditLog.details.like(f"%Email ID {email_rec.id}%")).count()
    assert audit_count >= 5

    # Cleanup
    db.delete(email_rec)
    db.delete(acc)
    db.commit()
    db.close()
    print("[PASS] test_workflow_state_machine passed!")

if __name__ == "__main__":
    test_workflow_state_machine()
