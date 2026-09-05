from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProcessedEmail, CTALog, ReplyLog, InboxAccount
from ..schemas import ProcessedEmailOut, CTALogOut, ReplyLogOut
from .dashboard import seed_default_activity

router = APIRouter(prefix="/api/emails", tags=["Processed Emails"])

from datetime import datetime, timezone

class EmailSyncPayload(BaseModel):
    correlation_id: str
    sender: str
    recipient: Optional[str] = "aiwithtarun1@gmail.com"
    subject: str
    status: str
    cta_url: Optional[str] = None
    received_at: Optional[str] = None

@router.post("/sync")
def sync_email_activity(payload: EmailSyncPayload, db: Session = Depends(get_db)):
    try:
        seed_default_activity(db)
        acc = db.query(InboxAccount).first()
        acc_id = acc.id if acc else 1
        
        recv_dt = None
        if payload.received_at:
            try:
                recv_dt = datetime.fromisoformat(payload.received_at.replace("Z", "+00:00"))
            except Exception:
                recv_dt = datetime.now(timezone.utc)

        existing = db.query(ProcessedEmail).filter(ProcessedEmail.correlation_id == payload.correlation_id).first()
        if existing:
            existing.status = payload.status
            if recv_dt:
                existing.received_at = recv_dt
            db.commit()
            return {"status": "updated", "id": existing.id}
        
        new_email = ProcessedEmail(
            correlation_id=payload.correlation_id,
            account_id=acc_id,
            message_id=f"{payload.correlation_id}@mail.gmail.com",
            sender=payload.sender,
            recipient=payload.recipient or "aiwithtarun1@gmail.com",
            subject=payload.subject,
            status=payload.status,
            received_at=recv_dt or datetime.now(timezone.utc)
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        if payload.cta_url:
            cta = CTALog(
                email_id=new_email.id,
                url=payload.cta_url,
                is_approved=payload.status in ["CTA_CLICKED", "COMPLETED"],
                status="COMPLETED" if payload.cta_url else payload.status
            )
            db.add(cta)
            db.commit()

        return {"status": "synced", "id": new_email.id}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}

@router.get("", response_model=List[ProcessedEmailOut])
def list_processed_emails(
    limit: int = Query(50, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    seed_default_activity(db)
    query = db.query(ProcessedEmail)
    if status:
        query = query.filter(ProcessedEmail.status == status)
    return query.order_by(ProcessedEmail.created_at.desc()).limit(limit).all()

@router.get("/{email_id}", response_model=ProcessedEmailOut)
def get_processed_email(email_id: int, db: Session = Depends(get_db)):
    email_rec = db.query(ProcessedEmail).filter(ProcessedEmail.id == email_id).first()
    if not email_rec:
        raise HTTPException(status_code=404, detail="Email record not found.")
    return email_rec

@router.get("/{email_id}/cta-logs", response_model=List[CTALogOut])
def get_cta_logs(email_id: int, db: Session = Depends(get_db)):
    return db.query(CTALog).filter(CTALog.email_id == email_id).all()

@router.get("/{email_id}/reply-logs", response_model=List[ReplyLogOut])
def get_reply_logs(email_id: int, db: Session = Depends(get_db)):
    return db.query(ReplyLog).filter(ReplyLog.email_id == email_id).all()

