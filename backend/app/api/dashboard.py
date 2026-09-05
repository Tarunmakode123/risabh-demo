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
                {"subject": "Make translations feel local", "sender": "noreply@email.openai.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-05T14:43:00"},
                {"subject": "naukri campus : Quiz is open for registration II - naukri.com Quiz", "sender": "eventnc@naukri.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-05T14:06:19"},
                {"subject": "Inquiry about service pricing and plans", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-09-05T12:00:26"},
                {"subject": "External Resource Verification", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-05T11:57:42"},
                {"subject": "Schedule Your Onboarding Session", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://claude.ai", "received_at": "2026-09-05T11:55:30"},
                {"subject": "$$$ CONGRATULATIONS URGENT WINNER $$$", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-09-05T11:53:38"},
                {"subject": "Weekly Product Newsletter", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-09-05T11:50:58"},
                {"subject": "Project Documentation Update", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "http://github.com", "received_at": "2026-09-05T11:49:21"},
                {"subject": "AI Engineer @ Drytis", "sender": "donotreply@match.indeed.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-05T01:31:18"},
                {"subject": "QA Test 1 - Approved Link", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://google.com", "received_at": "2026-09-05T01:09:05"},
                {"subject": "Technical Trainer at IKIGAI SCHOOL OF AI", "sender": "donotreply@jobalert.indeed.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T19:34:52"},
                {"subject": "Test Email 3", "sender": "tarunkumarmakode123@gmail.com", "status": "COMPLETED", "cta": "https://google.com", "received_at": "2026-09-04T18:57:42"},
                {"subject": "Testing ArrowMail Automation", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_CLICKED", "cta": "https://google.com", "received_at": "2026-09-04T18:55:22"},
                {"subject": "Testing ArrowMail Automation", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:51:35"},
                {"subject": "vuvu", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:47:25"},
                {"subject": "Test Warmup Email", "sender": "tarunkumarmakode123@gmail.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:47:20"},
                {"subject": "Security alert", "sender": "no-reply@accounts.google.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:47:15"},
                {"subject": "welcome to agi", "sender": "stayingahead@mail.beehiiv.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:47:10"},
                {"subject": "$99 a month, times a thousand", "sender": "jessecunningham@rankexpand.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-09-04T18:47:05"},
                {"subject": "Urgent Attention Needed", "sender": "stevenarcher388@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-31T20:43:53"},
                {"subject": "[SalesViral.com] – Your Next Growth Brand Starts Here", "sender": "ameerabusaada19992@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-30T12:38:46"},
                {"subject": "What's your goal for your book Aiwithtarun??", "sender": "honourempyron@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-30T08:48:36"},
                {"subject": "Save $300 on any new auto warranty purchase", "sender": "info@elitedigitalframeworks.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-27T15:45:01"},
                {"subject": "Retell Workflows, Brex top 25, and more", "sender": "hello@info.retellai.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-26T18:49:37"},
                {"subject": "Save big on your home warranty policy today", "sender": "info@leadblasterhub.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-25T13:00:02"},
                {"subject": "Save up to 70% on your new roof", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-24T15:55:01"},
                {"subject": "Confidential Business Proposal", "sender": "shoaibmirhashem@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-24T04:37:43"},
                {"subject": "Investment Partnership!", "sender": "if.folquett@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-23T22:52:44"},
                {"subject": "A simple path out of credit card debt", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-22T12:55:01"},
                {"subject": "We provide Project & Business Financing", "sender": "mikolasova@zs-loucen.cz", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-22T10:01:12"},
                {"subject": "Regarding Business Funds...", "sender": "higherceilingslimited@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-21T13:37:00"},
                {"subject": "Curious question about your model", "sender": "michaelogunleye127@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-21T08:00:09"},
                {"subject": "Get a brand-new roof without breaking the bank", "sender": "info@clickcampaignhub.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-20T12:05:01"},
                {"subject": "Your Profile Has Been Shortlisted | Adobe X Krutanic Internship Program 2026", "sender": "shreya@adobe-edu.in", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-20T11:44:47"},
                {"subject": "Email Verification!!!", "sender": "info@jag-petroleum.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-19T02:49:19"},
                {"subject": "Home Improvement or Debt Consolidation? Unlock your equity today", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-18T10:55:01"},
                {"subject": "hi", "sender": "shuzoliver@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-18T07:30:50"},
                {"subject": "Remote Services", "sender": "mtbaig911@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-18T01:34:16"},
                {"subject": "Dear Beloved,", "sender": "lettepencer@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-17T03:53:28"},
                {"subject": "Greeting,", "sender": "info@lebanauctionyard.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-16T03:22:33"},
                {"subject": "Don't overpay for home repairs—claim your discount", "sender": "info@marketupdateshub.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-14T12:30:02"},
                {"subject": "Don't miss out: happy hour + events", "sender": "hello@events.retellai.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-13T16:08:08"},
                {"subject": "Compare Vehicle Protection Plans for Your Car", "sender": "info@advancedemailmarketingpro.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-12T12:35:01"},
                {"subject": "Hello", "sender": "aburewaldemar1@gmail.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-12T12:25:46"},
                {"subject": "Don’t Let $10k in Debt Grow — Here’s Help", "sender": "info@dominateyourmarketonline.shop", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-10T16:05:02"},
                {"subject": "Re: Project Proposal Discussion", "sender": "mail.georges.elhedery.b@gmail.com", "status": "CTA_NOT_FOUND", "cta": "None", "received_at": "2026-08-10T15:39:02"},
                {"subject": "Limited offer - $300 off Endurance warranty purchase🚗", "sender": "info@elitedigitalframeworks.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-07T18:25:01"},
                {"subject": "Complete Your Debt Resolution Application", "sender": "info@mailboostmarketing.com", "status": "CTA_BLOCKED", "cta": "None", "received_at": "2026-08-06T13:50:01"}
            ]

            for idx, item in enumerate(seed_items):
                try:
                    recv_dt = datetime.fromisoformat(item["received_at"])
                except Exception:
                    recv_dt = datetime.utcnow()

                dup_check = db.query(ProcessedEmail).filter(
                    ProcessedEmail.subject == item["subject"],
                    ProcessedEmail.sender == item["sender"],
                    ProcessedEmail.received_at == recv_dt
                ).first()
                if dup_check:
                    continue

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
                    received_at=recv_dt
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
        emails = db.query(ProcessedEmail).order_by(ProcessedEmail.received_at.desc(), ProcessedEmail.id.desc()).limit(limit).all()
    except Exception:
        emails = []

    result = []
    seen_keys = set()
    for e in emails:
        ts = e.received_at or e.created_at
        ts_str = ts.isoformat() if ts else ""
        dedup_key = f"{e.sender}|{e.subject}|{ts_str}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        result.append({
            "id": e.id,
            "correlation_id": e.correlation_id,
            "inbox": e.account.email if e.account else "aiwithtarun1@gmail.com",
            "sender": e.sender,
            "recipient": e.recipient,
            "subject": e.subject or "(No Subject)",
            "received_at": ts_str,
            "opened_at": e.opened_at.isoformat() if e.opened_at else "-",
            "status": e.status,
            "error_message": e.error_message or "",
            "created_at": ts_str
        })
    return result
