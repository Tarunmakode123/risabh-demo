import os
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database import engine, get_db, Base
from app.models.schema import SeedAccount, WarmupLog, WarmupMetric
from app.services.imap_listener import IMAPService
from app.services.smtp_replyer import SMTPReplyService
from app.services.warmup_worker import warmup_worker

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.on_event("startup")
async def startup_event():
    # Start background worker automatically
    warmup_worker.start()


@app.on_event("shutdown")
async def shutdown_event():
    warmup_worker.stop()


# --- Pydantic Schemas ---
class SeedAccountCreate(BaseModel):
    email: str
    display_name: Optional[str] = ""
    imap_host: str
    imap_port: int = 993
    imap_use_ssl: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_use_ssl: bool = False
    password: str
    sender_filter: Optional[str] = ""
    auto_rescue_spam: bool = True
    auto_click_cta: bool = True
    auto_reply: bool = True


class ConnectionTestRequest(BaseModel):
    email: str
    password: str
    imap_host: str
    imap_port: int = 993
    imap_use_ssl: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_use_ssl: bool = False


# --- HTML Web Routes ---
@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.APP_NAME})


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    return templates.TemplateResponse("accounts.html", {"request": request, "app_name": settings.APP_NAME})


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request, "app_name": settings.APP_NAME})


# --- API Routes ---
@app.get("/api/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    accounts = db.query(SeedAccount).all()
    
    total_opened = sum(a.total_opened for a in accounts)
    total_clicked = sum(a.total_clicked for a in accounts)
    total_replied = sum(a.total_replied for a in accounts)
    total_spam_rescued = sum(a.total_spam_rescued for a in accounts)
    
    # Calculate ratios
    open_rate = round((total_clicked / total_opened * 100), 1) if total_opened > 0 else 0.0
    reply_rate = round((total_replied / total_opened * 100), 1) if total_opened > 0 else 0.0

    # Metrics history for charts (last 14 days)
    metrics = db.query(WarmupMetric).order_by(WarmupMetric.date.asc()).limit(14).all()
    
    chart_labels = [m.date for m in metrics]
    chart_opened = [m.opened_count for m in metrics]
    chart_clicked = [m.clicked_count for m in metrics]
    chart_replied = [m.replied_count for m in metrics]
    chart_spam = [m.spam_rescued_count for m in metrics]

    return {
        "summary": {
            "total_accounts": len(accounts),
            "active_accounts": sum(1 for a in accounts if a.is_active),
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_replied": total_replied,
            "total_spam_rescued": total_spam_rescued,
            "click_rate": open_rate,
            "reply_rate": reply_rate,
        },
        "charts": {
            "labels": chart_labels,
            "opened": chart_opened,
            "clicked": chart_clicked,
            "replied": chart_replied,
            "spam_rescued": chart_spam,
        }
    }


@app.get("/api/accounts")
def list_seed_accounts(db: Session = Depends(get_db)):
    accounts = db.query(SeedAccount).all()
    return accounts


@app.post("/api/accounts")
def create_seed_account(payload: SeedAccountCreate, db: Session = Depends(get_db)):
    existing = db.query(SeedAccount).filter(SeedAccount.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists.")

    account = SeedAccount(**payload.dict())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.delete("/api/accounts/{account_id}")
def delete_seed_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(SeedAccount).filter(SeedAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    db.delete(account)
    db.commit()
    return {"message": "Account deleted successfully"}


@app.post("/api/accounts/{account_id}/toggle")
def toggle_seed_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(SeedAccount).filter(SeedAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    account.is_active = not account.is_active
    db.commit()
    return {"id": account.id, "is_active": account.is_active}


@app.post("/api/accounts/test")
def test_account_connection(payload: ConnectionTestRequest):
    # Test IMAP
    imap_srv = IMAPService(
        host=payload.imap_host,
        port=payload.imap_port,
        email_address=payload.email,
        password=payload.password,
        use_ssl=payload.imap_use_ssl
    )
    imap_ok, imap_msg = imap_srv.test_connection()

    # Test SMTP
    smtp_srv = SMTPReplyService(
        host=payload.smtp_host,
        port=payload.smtp_port,
        email_address=payload.email,
        password=payload.password,
        use_ssl=payload.smtp_use_ssl
    )
    smtp_ok, smtp_msg = smtp_srv.test_connection()

    return {
        "success": imap_ok and smtp_ok,
        "imap": {"success": imap_ok, "message": imap_msg},
        "smtp": {"success": smtp_ok, "message": smtp_msg}
    }


@app.get("/api/logs")
def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(WarmupLog).order_by(WarmupLog.created_at.desc()).limit(limit).all()
    result = []
    for l in logs:
        result.append({
            "id": l.id,
            "account_email": l.seed_account.email if l.seed_account else "Unknown",
            "action": l.action,
            "subject": l.subject,
            "sender_email": l.sender_email,
            "details": l.details,
            "status": l.status,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else ""
        })
    return result


@app.get("/api/worker/status")
def get_worker_status():
    return {
        "is_running": warmup_worker.is_running,
        "poll_interval_seconds": warmup_worker.poll_interval
    }


@app.post("/api/worker/start")
def start_worker(interval: Optional[int] = Form(None)):
    warmup_worker.start(poll_interval=interval)
    return {"message": "Warmup worker started", "is_running": True}


@app.post("/api/worker/stop")
def stop_worker():
    warmup_worker.stop()
    return {"message": "Warmup worker stopped", "is_running": False}


@app.post("/api/worker/trigger")
async def trigger_worker():
    # Trigger one immediate check cycle asynchronously
    asyncio.create_task(warmup_worker.process_all_accounts())
    return {"message": "Immediate warmup cycle triggered for all active seed accounts"}
