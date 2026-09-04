from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import InboxAccount, User
from app.schemas import InboxAccountCreate, InboxAccountOut
from app.security import encrypt_credential, decrypt_credential
from app.dependencies import get_current_user
from app.services.imap_service import IMAPService
from app.services.smtp_service import SMTPService

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

    existing = db.query(InboxAccount).filter(InboxAccount.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists.")

    try:
        enc_pass = encrypt_credential(payload.password)
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
        raise HTTPException(status_code=400, detail=f"Failed to create inbox account: {str(e)}")

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
