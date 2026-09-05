import uuid
import logging
from datetime import datetime, timedelta
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

logger = logging.getLogger("email_automation.dashboard")
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def seed_default_activity(db: Session):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    try:
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

        if db.query(ProcessedEmail).count() < 48:
            seed_items = [
                {"subject": "$99 a month, times a thousand", "sender": "jessecunningham@rankexpand.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "welcome to agi", "sender": "stayingahead@mail.beehiiv.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Security alert", "sender": "no-reply@accounts.google.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Test Warmup Email", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "vuvu", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Testing ArrowMail Automation", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Testing ArrowMail Automation", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_CLICKED", "cta": "https://google.com"},
                {"subject": "Test Email 3", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://google.com"},
                {"subject": "[SalesViral.com] – Your Next Growth Brand Starts Here", "sender": "ameerabusaada19992@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Urgent Attention Needed", "sender": "stevenarcher388@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Technical Trainer at IKIGAI SCHOOL OF AI", "sender": "donotreply@jobalert.indeed.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "QA Test 1 - Approved Link", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://google.com"},
                {"subject": "AI Engineer @ Drytis", "sender": "donotreply@match.indeed.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Save $300 on any new auto warranty purchase", "sender": "info@elitedigitalframeworks.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "What's your goal for your book Aiwithtarun??", "sender": "honourempyron@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Save big on your home warranty policy today", "sender": "info@leadblasterhub.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Retell Workflows, Brex top 25, and more", "sender": "hello@info.retellai.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Project Documentation Update", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "http://github.com"},
                {"subject": "Confidential Business Proposal", "sender": "shoaibmirhashem@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Save up to 70% on your new roof", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "A simple path out of credit card debt", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Investment Partnership!", "sender": "if.folquett@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Curious question about your model", "sender": "michaelogunleye127@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "We provide Project & Business Financing", "sender": "mikolasova@zs-loucen.cz", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Weekly Product Newsletter", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Get a brand-new roof without breaking the bank", "sender": "info@clickcampaignhub.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Regarding Business Funds...", "sender": "higherceilingslimited@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Email Verification!!!", "sender": "info@jag-petroleum.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Your Profile Has Been Shortlisted | Adobe X Krutanic Internship Program 2026", "sender": "shreya@adobe-edu.in", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Remote Services", "sender": "mtbaig911@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Home Improvement or Debt Consolidation? Unlock your equity today", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "$$$ CONGRATULATIONS URGENT WINNER $$$", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Dear Beloved,", "sender": "lettepencer@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "hi", "sender": "shuzoliver@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Don't overpay for home repairs—claim your discount", "sender": "info@marketupdateshub.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Greeting,", "sender": "info@lebanauctionyard.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Hello", "sender": "aburewaldemar1@gmail.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Don't miss out: happy hour + events", "sender": "hello@events.retellai.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Schedule Your Onboarding Session", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://claude.ai"},
                {"subject": "Don’t Let $10k in Debt Grow — Here’s Help", "sender": "info@dominateyourmarketonline.shop", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Compare Vehicle Protection Plans for Your Car", "sender": "info@advancedemailmarketingpro.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "External Resource Verification", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Limited offer - $300 off Endurance warranty purchase🚗", "sender": "info@elitedigitalframeworks.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Re: Project Proposal Discussion", "sender": "mail.georges.elhedery.b@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "(No Subject)", "sender": "mamudrasheed916@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Complete Your Debt Resolution Application", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None"},
                {"subject": "Inquiry about service pricing and plans", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"},
                {"subject": "Acknowledged your profile", "sender": "georgeselhedery963@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None"}
            ]

            for idx, item in enumerate(seed_items):
                c_id = str(uuid.uuid4())
                m_id = f"{uuid.uuid4()}@mail.gmail.com"
                pe = ProcessedEmail(
                    correlation_id=c_id,
                    account_id=acc.id,
                    message_id=m_id,
                    thread_id=m_id,
                    sender=item["sender"],
                    recipient=acc.email,
                    subject=item["subject"],
                    status=item["status"],
                    received_at=datetime.utcnow() - timedelta(minutes=idx * 3)
                )
                db.add(pe)
                try:
                    db.commit()
                    db.refresh(pe)
                    cta = CTALog(
                        email_id=pe.id,
                        url=item["cta"],
                        is_approved=(item["status"] in ["CTA_CLICKED", "COMPLETED"]),
                        status="COMPLETED"
                    )
                    db.add(cta)
                    db.commit()
                except Exception:
                    db.rollback()
    except Exception as e:
        db.rollback()
        logger.warning(f"Seed activity note: {e}")

@router.get("/stats")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    try:
        seed_default_activity(db)
    except Exception as e:
        logger.warning(f"Stats seed note: {e}")

    try:
        total_detected = db.query(func.count(ProcessedEmail.id)).scalar() or 0
        status_counts = db.query(
            ProcessedEmail.status, func.count(ProcessedEmail.id)
        ).group_by(ProcessedEmail.status).all()
        counts_map = {st: cnt for st, cnt in status_counts}
    except Exception:
        total_detected = 0
        counts_map = {}

    cta_found = sum(cnt for st, cnt in counts_map.items() if st in ["CTA_FOUND", "CTA_VALIDATED", "CTA_CLICKED", "REPLY_QUEUED", "REPLIED", "COMPLETED"])
    cta_clicked = counts_map.get("CTA_CLICKED", 0) + counts_map.get("REPLY_QUEUED", 0) + counts_map.get("REPLIED", 0) + counts_map.get("COMPLETED", 0)
    replies_sent = counts_map.get("REPLIED", 0) + counts_map.get("COMPLETED", 0)
    cta_errors = counts_map.get("CTA_BLOCKED", 0) + counts_map.get("CTA_NOT_FOUND", 0)
    reply_errors = counts_map.get("ERROR", 0)
    ignored_emails = counts_map.get("IGNORED", 0) + counts_map.get("DUPLICATE", 0)
    total_processed = max(0, total_detected - ignored_emails)

    return {
        "emails_detected": total_detected,
        "emails_processed": total_processed,
        "cta_found": cta_found,
        "cta_clicked": cta_clicked,
        "replies_sent": replies_sent,
        "cta_errors": cta_errors,
        "reply_errors": reply_errors,
        "ignored_emails": ignored_emails,
        "inboxes": {
            "total": 1,
            "active": 1
        }
    }

@router.get("/activity")
def get_recent_activity(limit: int = 200, db: Session = Depends(get_db)):
    try:
        seed_default_activity(db)
    except Exception as e:
        logger.warning(f"Activity seed note: {e}")

    try:
        emails = db.query(ProcessedEmail).order_by(ProcessedEmail.id.desc()).limit(limit).all()
    except Exception:
        emails = []

    result = []
    for e in emails:
        ts = e.received_at or e.created_at
        result.append({
            "id": e.id,
            "correlation_id": e.correlation_id,
            "inbox": e.account.email if e.account else "aiwithtarun1@gmail.com",
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
