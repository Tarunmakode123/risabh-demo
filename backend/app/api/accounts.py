from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import InboxAccount, ProcessedEmail, CTALog, ReplyLog
from app.schemas import InboxAccountCreate, InboxAccountOut
from app.security import encrypt_credential, decrypt_credential
from app.dependencies import get_current_user
from app.services.imap_service import IMAPService
from app.services.smtp_service import SMTPService
from app.services.deduplication import DeduplicationService
from app.services.cta_service import CTAService
from app.services.workflow_service import WorkflowStateService

router = APIRouter(prefix="/api/accounts", tags=["Inbox Accounts"])

@router.get("", response_model=List[InboxAccountOut])
def list_accounts(db: Session = Depends(get_db)):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    return db.query(InboxAccount).all()

@router.post("", response_model=InboxAccountOut)
def create_account(payload: InboxAccountCreate, db: Session = Depends(get_db)):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    try:
        enc_pass = encrypt_credential(payload.password)
        existing = db.query(InboxAccount).filter(InboxAccount.email == payload.email).first()
        if existing:
            existing.username = payload.username
            existing.encrypted_password = enc_pass
            existing.imap_host = payload.imap_host
            existing.imap_port = payload.imap_port
            existing.smtp_host = payload.smtp_host
            existing.smtp_port = payload.smtp_port
            existing.use_ssl = payload.use_ssl
            existing.folder = payload.folder
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        acc = InboxAccount(
            email=payload.email,
            imap_host=payload.imap_host,
            imap_port=payload.imap_port,
            smtp_host=payload.smtp_host,
            smtp_port=payload.smtp_port,
            username=payload.username,
            encrypted_password=enc_pass,
            use_ssl=payload.use_ssl,
            folder=payload.folder,
            is_active=True
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)
        return acc
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create or update inbox account: {str(e)}")

@router.post("/{account_id}/sync-now")
def sync_account_emails_now(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")

    plain_pass = decrypt_credential(acc.encrypted_password)
    service = IMAPService(
        host=acc.imap_host,
        port=acc.imap_port,
        username=acc.username,
        password=plain_pass,
        use_ssl=acc.use_ssl,
        folder=acc.folder
    )

    # Fetch new messages directly via IMAP
    messages = service.fetch_new_messages(limit=10)
    synced_count = 0

    for msg in messages:
        # Check deduplication
        is_dup = DeduplicationService.is_duplicate(db, acc.id, msg.message_id)
        if is_dup:
            continue

        # Create processed email record
        email_rec, err = WorkflowStateService.create_initial_email_record(db, acc.id, msg)
        if not email_rec:
            continue

        # Extract & validate CTA
        candidates = CTAService.extract_candidate_links(msg.html_body or msg.text_body or "")
        best_cta, cta_status = CTAService.find_best_cta(candidates)

        if best_cta:
            is_app, app_reason = CTAService.validate_cta_domain(best_cta)
            CTAService.log_cta_attempt(
                db=db,
                email_id=email_rec.id,
                url=best_cta,
                is_approved=is_app,
                status="COMPLETED" if is_app else "BLOCKED"
            )
            if is_app:
                WorkflowStateService.transition_state(db, email_rec.id, "CTA_CLICKED")
            else:
                WorkflowStateService.transition_state(db, email_rec.id, "CTA_BLOCKED", error_message=app_reason)
        else:
            WorkflowStateService.transition_state(db, email_rec.id, "CTA_NOT_FOUND")

        synced_count += 1

    return {"success": True, "synced_count": synced_count, "total_fetched": len(messages)}

@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")
    db.delete(acc)
    db.commit()
    return {"message": "Inbox account deleted"}

@router.post("/{account_id}/toggle")
def toggle_account(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")
    acc.is_active = not acc.is_active
    db.commit()
    return {"id": acc.id, "is_active": acc.is_active}

@router.post("/{account_id}/test-imap")
def test_imap(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")

    plain_pass = decrypt_credential(acc.encrypted_password)
    service = IMAPService(
        host=acc.imap_host,
        port=acc.imap_port,
        username=acc.username,
        password=plain_pass,
        use_ssl=acc.use_ssl,
        folder=acc.folder
    )
    ok, msg = service.test_connection()
    return {"success": ok, "message": msg}

@router.post("/{account_id}/test-smtp")
def test_smtp(account_id: int, db: Session = Depends(get_db)):
    acc = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")

    plain_pass = decrypt_credential(acc.encrypted_password)
    service = SMTPService(
        host=acc.smtp_host,
        port=acc.smtp_port,
        username=acc.username,
        password=plain_pass,
        use_ssl=False
    )
    ok, msg = service.test_connection()
    return {"success": ok, "message": msg}
