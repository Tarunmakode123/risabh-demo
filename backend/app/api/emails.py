from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ProcessedEmail, CTALog, ReplyLog
from app.schemas import ProcessedEmailOut, CTALogOut, ReplyLogOut

router = APIRouter(prefix="/api/emails", tags=["Processed Emails"])

@router.get("", response_model=List[ProcessedEmailOut])
def list_processed_emails(
    limit: int = Query(50, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
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
