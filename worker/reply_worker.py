import time
import random
import logging
from celery_app import celery_app
from app.database import SessionLocal
from app.models import ProcessedEmail, ReplyLog, ReplyTemplate, InboxAccount, SystemSettings
from app.security import decrypt_credential
from app.services.smtp_service import SMTPService
from app.services.deduplication import DeduplicationService
from app.services.workflow_service import WorkflowService

logger = logging.getLogger("email_automation.reply_worker")

@celery_app.task(name="worker.reply_worker.execute_reply_task")
def execute_reply_task(email_id: int):
    db = SessionLocal()
    try:
        # Pre-action check: Kill Switch
        if WorkflowService.is_system_paused(db):
            logger.warning(f"Kill Switch active. Pausing Reply task for email {email_id}.")
            return

        # Atomic State Acquisition
        email_record = DeduplicationService.acquire_email_atomically(db, email_id)
        if not email_record:
            logger.warning(f"Could not acquire atomic lock for email_id {email_id}. Skipping.")
            return

        # Duplicate Reply Protection Check
        if email_record.status in ["REPLIED", "COMPLETED"]:
            logger.info(f"Email ID {email_id} has already been replied to. Skipping.")
            return

        WorkflowService.transition_state(db, email_record, "REPLY_QUEUED")

        # Configurable Reply Delay
        settings_rec = db.query(SystemSettings).first()
        min_delay = settings_rec.min_reply_delay if settings_rec else 5
        max_delay = settings_rec.max_reply_delay if settings_rec else 15
        delay_seconds = random.randint(min_delay, max_delay)

        logger.info(f"Waiting {delay_seconds} seconds before sending reply for email {email_id}...")
        time.sleep(delay_seconds)

        # Re-check Kill Switch after delay
        if WorkflowService.is_system_paused(db):
            logger.warning(f"Kill Switch activated during reply delay for email {email_id}. Aborting reply.")
            return

        # Fetch active Reply Template
        template = db.query(ReplyTemplate).filter(ReplyTemplate.is_active == True).first()
        reply_body = template.body if template else "Thanks, received it."

        # Fetch Inbox Account Credentials
        account = db.query(InboxAccount).filter(InboxAccount.id == email_record.account_id).first()
        if not account:
            WorkflowService.transition_state(db, email_record, "ERROR", error_msg="Inbox account not found")
            return

        plain_pass = decrypt_credential(account.encrypted_password)
        smtp_srv = SMTPService(
            host=account.smtp_host,
            port=account.smtp_port,
            username=account.username,
            password=plain_pass,
            use_ssl=False
        )

        success, msg = smtp_srv.send_threaded_reply(
            to_email=email_record.sender,
            original_subject=email_record.subject or "",
            in_reply_to=email_record.message_id,
            references_header=email_record.thread_id or email_record.message_id,
            reply_body=reply_body,
            correlation_id=email_record.correlation_id
        )

        db.add(ReplyLog(
            email_id=email_id,
            in_reply_to=email_record.message_id,
            references_header=email_record.thread_id or email_record.message_id,
            reply_body=reply_body,
            delay_seconds=delay_seconds,
            status="SENT" if success else "FAILED",
            error_message=None if success else msg
        ))
        db.commit()

        if success:
            WorkflowService.transition_state(db, email_record, "REPLIED")
            WorkflowService.transition_state(db, email_record, "COMPLETED")
        else:
            WorkflowService.transition_state(db, email_record, "ERROR", error_msg=msg)

    except Exception as e:
        logger.error(f"Error executing reply task for email {email_id}: {e}")
        email_record = db.query(ProcessedEmail).filter(ProcessedEmail.id == email_id).first()
        if email_record:
            WorkflowService.transition_state(db, email_record, "ERROR", error_msg=str(e))
    finally:
        db.close()
