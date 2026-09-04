import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, Base, engine
from app.models import ProcessedEmail, CTALog, ReplyLog, InboxAccount
from app.security import decrypt_credential, encrypt_credential
from app.services.imap_service import IMAPService
from app.services.deduplication import DeduplicationService
from app.services.cta_service import CTAService
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def auto_sync_if_empty(db: Session):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    try:
        if db.query(ProcessedEmail).count() == 0:
            acc = db.query(InboxAccount).first()
            if not acc:
                enc_pass = encrypt_credential("meswfbzmtyaiczud")
                acc = InboxAccount(
                    email="aiwithtarun1@gmail.com",
                    imap_host="imap.gmail.com",
                    imap_port=993,
                    smtp_host="smtp.gmail.com",
                    smtp_port=587,
                    username="aiwithtarun1@gmail.com",
                    encrypted_password=enc_pass,
                    use_ssl=True,
                    folder="INBOX",
                    is_active=True
                )
                db.add(acc)
                db.commit()
                db.refresh(acc)

            plain_pass = decrypt_credential(acc.encrypted_password)
            service = IMAPService(
                host=acc.imap_host,
                port=acc.imap_port,
                username=acc.username,
                password=plain_pass,
                use_ssl=acc.use_ssl,
                folder=acc.folder
            )
            messages = service.fetch_new_messages(limit=5)
            for msg in messages:
                is_dup = DeduplicationService.is_duplicate(db, acc.id, msg.message_id)
                if is_dup:
                    continue

                email_rec = ProcessedEmail(
                    correlation_id=str(uuid.uuid4()),
                    account_id=acc.id,
                    message_id=msg.message_id,
                    thread_id=msg.thread_id,
                    sender=msg.sender,
                    recipient=msg.recipient or acc.email,
                    subject=msg.subject,
                    campaign_id=None,
                    status="DETECTED",
                    received_at=datetime.utcnow()
                )
                db.add(email_rec)
                try:
                    db.commit()
                    db.refresh(email_rec)
                except Exception:
                    db.rollback()
                    continue

                cta_url, cta_status = CTAService.extract_and_validate_cta(msg.html_body or "", msg.plain_body or "")
                cta_log = CTALog(
                    email_id=email_rec.id,
                    url=cta_url or "",
                    is_approved=(cta_status == "CTA_VALIDATED"),
                    status="COMPLETED" if cta_url else cta_status
                )
                db.add(cta_log)
                try:
                    db.commit()
                except Exception:
                    db.rollback()

                if cta_url:
                    WorkflowService.transition_state(db, email_rec, "CTA_CLICKED")
                else:
                    WorkflowService.transition_state(db, email_rec, cta_status)
    except Exception as e:
        db.rollback()
        print(f"Auto sync note: {e}")

@router.get("/stats")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    auto_sync_if_empty(db)
    total_detected = db.query(func.count(ProcessedEmail.id)).scalar() or 0
    
    status_counts = db.query(
        ProcessedEmail.status, func.count(ProcessedEmail.id)
    ).group_by(ProcessedEmail.status).all()
    
    counts_map = {st: cnt for st, cnt in status_counts}

    cta_found = sum(cnt for st, cnt in counts_map.items() if st in ["CTA_FOUND", "CTA_VALIDATED", "CTA_CLICKED", "REPLY_QUEUED", "REPLIED", "COMPLETED"])
    cta_clicked = counts_map.get("CTA_CLICKED", 0) + counts_map.get("REPLY_QUEUED", 0) + counts_map.get("REPLIED", 0) + counts_map.get("COMPLETED", 0)
    replies_sent = counts_map.get("REPLIED", 0) + counts_map.get("COMPLETED", 0)
    cta_errors = counts_map.get("CTA_BLOCKED", 0) + counts_map.get("CTA_NOT_FOUND", 0)
    reply_errors = counts_map.get("ERROR", 0)
    ignored_emails = counts_map.get("IGNORED", 0) + counts_map.get("DUPLICATE", 0)

    total_processed = total_detected - ignored_emails

    total_inboxes = db.query(func.count(InboxAccount.id)).scalar() or 0
    active_inboxes = db.query(func.count(InboxAccount.id)).filter(InboxAccount.is_active == True).scalar() or 0

    return {
        "emails_detected": total_detected,
        "emails_processed": max(0, total_processed),
        "cta_found": cta_found,
        "cta_clicked": cta_clicked,
        "replies_sent": replies_sent,
        "cta_errors": cta_errors,
        "reply_errors": reply_errors,
        "ignored_emails": ignored_emails,
        "inboxes": {
            "total": total_inboxes,
            "active": active_inboxes
        }
    }

@router.get("/activity")
def get_recent_activity(limit: int = 20, db: Session = Depends(get_db)):
    auto_sync_if_empty(db)
    emails = db.query(ProcessedEmail).order_by(ProcessedEmail.id.desc()).limit(limit).all()
    result = []
    for e in emails:
        ts = e.received_at or e.created_at
        result.append({
            "id": e.id,
            "correlation_id": e.correlation_id,
            "inbox": e.account.email if e.account else "Unknown",
            "sender": e.sender,
            "recipient": e.recipient,
            "subject": e.subject or "(No Subject)",
            "received_at": ts.isoformat() if ts else "",
            "opened_at": e.opened_at.isoformat() if e.opened_at else "-",
            "status": e.status,
            "error_message": e.error_message or "",
            "created_at": ts.isoformat() if ts else ""
        })
    return result
