import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import ProcessedEmail
from app.config import settings

logger = logging.getLogger("email_automation.deduplication")

class DeduplicationService:
    @staticmethod
    def is_duplicate(db: Session, account_id: int, message_id: str) -> bool:
        if not message_id:
            return False
        existing = db.query(ProcessedEmail).filter(
            ProcessedEmail.account_id == account_id,
            ProcessedEmail.message_id == message_id
        ).first()
        return existing is not None

    @staticmethod
    def is_campaign_allowed(sender_email: str, allowed_sender_domains: List[str] = None) -> bool:
        if allowed_sender_domains is None:
            allowed_sender_domains = settings.ALLOWED_SENDER_DOMAINS

        if not allowed_sender_domains:
            return True

        sender_lower = sender_email.lower().strip()
        for domain in allowed_sender_domains:
            if domain.lower() in sender_lower:
                return True

        logger.info(f"Campaign email sender '{sender_email}' not in ALLOWED_SENDER_DOMAINS ({allowed_sender_domains})")
        return False

    @staticmethod
    def acquire_email_atomically(db: Session, email_id: int) -> Optional[ProcessedEmail]:
        """
        Atomic State Acquisition: Uses SELECT ... FOR UPDATE SKIP LOCKED
        Prevents multiple Celery workers from claiming or processing the same email concurrently.
        """
        try:
            email_record = db.query(ProcessedEmail).filter(
                ProcessedEmail.id == email_id
            ).with_for_update(skip_locked=True).first()
            return email_record
        except Exception as e:
            logger.error(f"Error acquiring atomic lock for email_id {email_id}: {e}")
            return None
