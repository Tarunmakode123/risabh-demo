import uuid
import logging
from celery_app import celery_app
from app.database import SessionLocal
from app.models import InboxAccount, ProcessedEmail, EmailLink
from app.security import decrypt_credential
from app.services.imap_service import IMAPService
from app.services.deduplication import DeduplicationService
from app.services.workflow_service import WorkflowService

logger = logging.getLogger("email_automation.imap_worker")

@celery_app.task(name="worker.imap_worker.poll_all_inboxes_task")
def poll_all_inboxes_task():
    db = SessionLocal()
    try:
        if WorkflowService.is_system_paused(db):
            logger.info("System is PAUSED (Kill Switch active). Skipping IMAP polling.")
            return

        active_accounts = db.query(InboxAccount).filter(InboxAccount.is_active == True).all()
        for account in active_accounts:
            poll_single_inbox_task.delay(account.id)
    finally:
        db.close()

@celery_app.task(name="worker.imap_worker.poll_single_inbox_task")
def poll_single_inbox_task(account_id: int):
    db = SessionLocal()
    try:
        if WorkflowService.is_system_paused(db):
            return

        account = db.query(InboxAccount).filter(InboxAccount.id == account_id).first()
        if not account or not account.is_active:
            return

        plain_pass = decrypt_credential(account.encrypted_password)
        imap_srv = IMAPService(
            host=account.imap_host,
            port=account.imap_port,
            username=account.username,
            password=plain_pass,
            use_ssl=account.use_ssl,
            folder=account.folder
        )

        unseen_messages = imap_srv.fetch_new_messages(limit=15)
        for msg in unseen_messages:
            # 1. Message-ID Deduplication
            if DeduplicationService.is_duplicate(db, account.id, msg.message_id):
                logger.info(f"Duplicate Message-ID '{msg.message_id}' detected for account {account.email}. Skipping.")
                continue

            correlation_id = str(uuid.uuid4())

            # 2. Campaign Sender Domain Check
            is_campaign = DeduplicationService.is_campaign_allowed(msg.sender)
            initial_status = "DETECTED" if is_campaign else "IGNORED"

            # Create ProcessedEmail Record
            email_record = ProcessedEmail(
                correlation_id=correlation_id,
                account_id=account.id,
                message_id=msg.message_id,
                thread_id=msg.thread_id,
                sender=msg.sender,
                recipient=msg.recipient,
                subject=msg.subject,
                status=initial_status,
                error_message=None if is_campaign else "Sender not in ALLOWED_SENDER_DOMAINS"
            )
            db.add(email_record)
            db.commit()
            db.refresh(email_record)

            # Store Anchor Links
            for link in msg.links:
                db.add(EmailLink(
                    email_id=email_record.id,
                    anchor_text=link.anchor_text,
                    url=link.url
                ))
            db.commit()

            logger.info(f"Detected new email ID {email_record.id} (Correlation ID: {correlation_id}, Status: {initial_status})")

            # Queue Workflow processing if campaign matches
            if is_campaign:
                from worker.workflow_worker import process_email_workflow_task
                process_email_workflow_task.delay(email_record.id, msg.plain_body, msg.html_body)

    except Exception as e:
        logger.error(f"Error in poll_single_inbox_task for account_id {account_id}: {e}")
    finally:
        db.close()
