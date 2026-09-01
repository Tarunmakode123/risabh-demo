import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import ProcessedEmail, SystemSettings, AuditLog

logger = logging.getLogger("email_automation.workflow")

VALID_STATES = {
    "DETECTED", "PARSING", "PARSED", "CTA_FOUND", "CTA_VALIDATED",
    "CTA_CLICKED", "REPLY_QUEUED", "REPLIED", "COMPLETED",
    "IGNORED", "CTA_NOT_FOUND", "CTA_BLOCKED", "DUPLICATE", "ERROR"
}

class WorkflowService:
    @staticmethod
    def is_system_paused(db: Session) -> bool:
        settings_rec = db.query(SystemSettings).first()
        if settings_rec and settings_rec.is_paused:
            return True
        return False

    @classmethod
    def transition_state(
        cls,
        db: Session,
        email_record: ProcessedEmail,
        target_state: str,
        error_msg: Optional[str] = None
    ) -> bool:
        """
        Transactional state transition on PostgreSQL authoritative state model.
        Logs state transitions and updates timestamps.
        """
        if target_state not in VALID_STATES:
            logger.error(f"Invalid target state transition attempted: '{target_state}'")
            return False

        old_state = email_record.status
        email_record.status = target_state
        email_record.updated_at = datetime.utcnow()

        if error_msg:
            email_record.error_message = error_msg

        if target_state == "PARSED" and not email_record.opened_at:
            email_record.opened_at = datetime.utcnow()

        db.add(AuditLog(
            action=f"STATE_TRANSITION:{old_state}->{target_state}",
            details=f"Email ID {email_record.id} (Correlation ID: {email_record.correlation_id}). Message: {error_msg or 'OK'}"
        ))

        try:
            db.commit()
            db.refresh(email_record)
            logger.info(f"[Workflow Transition] Email ID {email_record.id}: {old_state} -> {target_state} (Correlation ID: {email_record.correlation_id})")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit workflow state transition for email {email_record.id}: {e}")
            return False
