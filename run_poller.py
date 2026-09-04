import sys
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "backend"))

import time
import uuid
import logging
from datetime import datetime
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
                    received_at=datetime.utcnow()
                )
                db.add(email_rec)
                try:
                    db.commit()
                    db.refresh(email_rec)
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
                    
                    # Send Threaded SMTP Auto-Reply
                    smtp_svc = SMTPService(
                        host=acc.smtp_host,
                        port=acc.smtp_port,
                        username=acc.username,
                        password=plain_pass,
                        use_ssl=False
                    )
                    reply_body = f"Thanks for sharing this! Received your email regarding '{msg.subject}'."
                    success, reply_msg, sent_msg_id = smtp_svc.send_threaded_reply(
                        recipient=msg.sender,
                        subject=msg.subject,
                        reply_body=reply_body,
                        in_reply_to=msg.in_reply_to or msg.message_id,
                        references=msg.references_header or msg.message_id,
                        correlation_id=correlation_id
                    )

                    reply_log = ReplyLog(
                        email_id=email_rec.id,
                        in_reply_to=msg.message_id,
                        reply_body=reply_body,
                        delay_seconds=5,
                        sent_at=datetime.utcnow() if success else None,
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
                        logger.info(f"SUCCESS: Auto-reply sent to {msg.sender} for email '{msg.subject}'")
                    else:
                        WorkflowService.transition_state(db, email_rec, "ERROR", error_msg=reply_msg)
                else:
                    WorkflowService.transition_state(db, email_rec, cta_status)

    except Exception as e:
        logger.error(f"Poller iteration error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("==================================================")
    logger.info(" Starting Standalone Live Email Poller & Replier ")
    logger.info(" Press Ctrl+C to stop ")
    logger.info("==================================================")
    while True:
        poll_and_process()
        logger.info("Waiting 15 seconds until next poll cycle...")
        time.sleep(15)
