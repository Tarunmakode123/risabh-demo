from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import ProcessedEmail, CTALog, ReplyLog, InboxAccount

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_metrics(db: Session = Depends(get_db)):
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
    emails = db.query(ProcessedEmail).order_by(ProcessedEmail.created_at.desc()).limit(limit).all()
    result = []
    for e in emails:
        result.append({
            "id": e.id,
            "correlation_id": e.correlation_id,
            "inbox": e.account.email if e.account else "Unknown",
            "sender": e.sender,
            "recipient": e.recipient,
            "subject": e.subject or "(No Subject)",
            "received_at": e.received_at.strftime("%Y-%m-%d %H:%M:%S") if e.received_at else "",
            "opened_at": e.opened_at.strftime("%Y-%m-%d %H:%M:%S") if e.opened_at else "-",
            "status": e.status,
            "error_message": e.error_message or "",
            "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else ""
        })
    return result
