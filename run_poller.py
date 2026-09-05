import sys
import os
import json
import urllib.request
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "backend"))

import time
import uuid
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from app.database import SessionLocal, engine, Base
from app.models import InboxAccount, ProcessedEmail, CTALog, ReplyLog
from app.security import decrypt_credential, encrypt_credential
from app.services.imap_service import IMAPService
from app.services.smtp_service import SMTPService
from app.services.deduplication import DeduplicationService
from app.services.cta_service import CTAService
from app.services.workflow_service import WorkflowService
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("email_poller")

def sync_to_remote_dashboard(correlation_id, sender, recipient, subject, status, cta_url="", received_at=None):
    try:
        remote_url = os.environ.get("VERCEL_API_URL", "https://risabh-demo.vercel.app") + "/api/emails/sync"
        payload_dict = {
            "correlation_id": correlation_id,
            "sender": sender,
            "recipient": recipient or "aiwithtarun1@gmail.com",
            "subject": subject,
            "status": status,
            "cta_url": cta_url or ""
        }
        if received_at:
            payload_dict["received_at"] = received_at
        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(remote_url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.debug(f"Dashboard sync note: {e}")

def sync_all_existing_local_emails():
    db = SessionLocal()
    try:
        emails = db.query(ProcessedEmail).order_by(ProcessedEmail.id.asc()).all()
        for e in emails:
            cta = db.query(CTALog).filter(CTALog.email_id == e.id).first()
            cta_url = cta.url if cta else ""
            ts = e.received_at or e.created_at
            ts_str = ts.isoformat() if ts else None
            sync_to_remote_dashboard(
                correlation_id=e.correlation_id,
                sender=e.sender,
                recipient=e.recipient,
                subject=e.subject,
                status=e.status,
                cta_url=cta_url,
                received_at=ts_str
            )
    except Exception as e:
        logger.debug(f"Initial sync note: {e}")
    finally:
        db.close()

def poll_and_process():
    # Ensure database schema exists
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    db = SessionLocal()
    try:
        # Get active test inbox accounts
        accounts = db.query(InboxAccount).filter(InboxAccount.is_active == True).all()

        if not accounts:
            logger.info("No active test inbox accounts found. Seeding default aiwithtarun1@gmail.com...")
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
            accounts = [acc]

        for acc in accounts:
            logger.info(f"Checking IMAP inbox for {acc.email}...")
            plain_pass = decrypt_credential(acc.encrypted_password)

            imap_svc = IMAPService(
                host=acc.imap_host,
                port=acc.imap_port,
                username=acc.username,
                password=plain_pass,
                use_ssl=acc.use_ssl,
                folder=acc.folder
            )

            # Rescue spam emails before checking inbox
            try:
                rescued_count = imap_svc.rescue_spam_emails()
                if rescued_count > 0:
                    logger.info(f"Rescued {rescued_count} email(s) from Spam to INBOX")
            except Exception as e:
                logger.debug(f"Spam rescue note: {e}")

            messages = imap_svc.fetch_new_messages(limit=5)
            logger.info(f"Fetched {len(messages)} recent message(s) for {acc.email}")

            for msg in messages:
                if DeduplicationService.is_duplicate(db, acc.id, msg.message_id):
                    logger.info(f"Skipping duplicate Message-ID: {msg.message_id}")
                    continue

                correlation_id = str(uuid.uuid4())
                logger.info(f"Processing new email: Subject='{msg.subject}' Sender='{msg.sender}' CorrelationID='{correlation_id}'")

                email_rec = ProcessedEmail(
                    correlation_id=correlation_id,
                    account_id=acc.id,
                    message_id=msg.message_id,
                    thread_id=msg.thread_id,
                    sender=msg.sender,
                    recipient=msg.recipient or acc.email,
                    subject=msg.subject,
                    status="DETECTED",
                    received_at=msg.parsed_date or datetime.utcnow()
                )
                db.add(email_rec)
                ts = email_rec.received_at or datetime.utcnow()
                if ts.tzinfo:
                    ts = ts.replace(tzinfo=None)
                rec_ts = ts.isoformat()
                try:
                    db.commit()
                    db.refresh(email_rec)
                    sync_to_remote_dashboard(correlation_id, msg.sender, msg.recipient, msg.subject, "DETECTED", received_at=rec_ts)
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving email record: {e}")
                    continue

                # Extract & Validate CTA
                cta_url, cta_status = CTAService.extract_and_validate_cta(msg.html_body or "", msg.plain_body or "")
                logger.info(f"CTA extraction result: URL='{cta_url}' Status='{cta_status}'")

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
                    sync_to_remote_dashboard(correlation_id, msg.sender, msg.recipient, msg.subject, "CTA_CLICKED", cta_url, received_at=rec_ts)
                    
                    # Send Threaded SMTP Auto-Reply
                    smtp_svc = SMTPService(
                        host=acc.smtp_host,
                        port=acc.smtp_port,
                        username=acc.username,
                        password=plain_pass,
                        use_ssl=False
                    )
                    reply_body = f"Thanks for sharing this! Received your email regarding '{msg.subject}'."
                    success, reply_msg = smtp_svc.send_threaded_reply(
                        to_email=msg.sender,
                        original_subject=msg.subject or "",
                        in_reply_to=msg.in_reply_to or msg.message_id,
                        references_header=msg.references_header or msg.message_id,
                        reply_body=reply_body,
                        correlation_id=correlation_id
                    )

                    reply_log = ReplyLog(
                        email_id=email_rec.id,
                        in_reply_to=msg.message_id,
                        reply_body=reply_body,
                        delay_seconds=5,
                        sent_at=datetime.now(timezone.utc) if success else None,
                        status="SENT" if success else "FAILED",
                        error_message=None if success else reply_msg
                    )
                    db.add(reply_log)
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()

                    if success:
                        WorkflowService.transition_state(db, email_rec, "COMPLETED")
                        sync_to_remote_dashboard(correlation_id, msg.sender, msg.recipient, msg.subject, "COMPLETED", cta_url, received_at=rec_ts)
                        logger.info(f"SUCCESS: Auto-reply sent to {msg.sender} for email '{msg.subject}'")
                    else:
                        WorkflowService.transition_state(db, email_rec, "ERROR", error_msg=reply_msg)
                        sync_to_remote_dashboard(correlation_id, msg.sender, msg.recipient, msg.subject, "ERROR", cta_url, received_at=rec_ts)
                else:
                    WorkflowService.transition_state(db, email_rec, cta_status)
                    sync_to_remote_dashboard(correlation_id, msg.sender, msg.recipient, msg.subject, cta_status, received_at=rec_ts)

    except Exception as e:
        logger.error(f"Poller iteration error: {e}")
    finally:
        db.close()

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check HTTP server listening on 0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health server failed to start: {e}")

if __name__ == "__main__":
    logger.info("==================================================")
    logger.info(" Starting Standalone Live Email Poller & Replier ")
    logger.info(" Press Ctrl+C to stop ")
    logger.info("==================================================")
    
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    sync_all_existing_local_emails()
    while True:
        poll_and_process()
        logger.info("Waiting 15 seconds until next poll cycle...")
        time.sleep(15)

