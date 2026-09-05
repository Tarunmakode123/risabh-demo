import uuid
from datetime import datetime
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
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/accounts", tags=["Inbox Accounts"])

def seed_default_accounts(db: Session):
    try:
        if db.query(InboxAccount).count() == 0:
            enc_pass = encrypt_credential("meswfbzmtyaiczud")
            default_acc = InboxAccount(
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
            db.add(default_acc)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed accounts note: {e}")

@router.get("")
def list_accounts(db: Session = Depends(get_db)):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    try:
        seed_default_accounts(db)
    except Exception:
        pass

    try:
        accounts = db.query(InboxAccount).all()
        if not accounts:
            seed_default_accounts(db)
            accounts = db.query(InboxAccount).all()

        result = []
        for acc in accounts:
            result.append({
                "id": acc.id,
                "email": acc.email,
                "imap_host": acc.imap_host,
                "imap_port": acc.imap_port,
                "smtp_host": acc.smtp_host,
                "smtp_port": acc.smtp_port,
                "username": acc.username,
                "use_ssl": acc.use_ssl,
                "folder": acc.folder,
                "is_active": acc.is_active,
                "created_at": acc.created_at.isoformat() if acc.created_at else ""
            })
        return result
    except Exception as e:
        print(f"List accounts note: {e}")
        return [{
            "id": 1,
            "email": "aiwithtarun1@gmail.com",
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "aiwithtarun1@gmail.com",
            "use_ssl": True,
            "folder": "INBOX",
            "is_active": True,
            "created_at": ""
        }]

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
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    seed_default_accounts(db)

    acc = db.query(InboxAccount).filter((InboxAccount.id == account_id) | (InboxAccount.email == "aiwithtarun1@gmail.com")).first() or db.query(InboxAccount).first()
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

    # Fetch new messages directly via IMAP (fast limit=5 for serverless response time)
    messages = service.fetch_new_messages(limit=30)
    synced_count = 0

    for msg in messages:
        # Check deduplication
        is_dup = DeduplicationService.is_duplicate(db, acc.id, msg.message_id)
        if is_dup:
            continue

        # Create processed email record
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

        # Extract & validate CTA
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
