import logging
from celery_app import celery_app
from app.database import SessionLocal
from app.models import ProcessedEmail
from app.services.workflow_service import WorkflowService
from worker.cta_worker import execute_cta_task

logger = logging.getLogger("email_automation.workflow_worker")

@celery_app.task(name="worker.workflow_worker.process_email_workflow_task")
def process_email_workflow_task(email_id: int, plain_body: str = "", html_body: str = ""):
    db = SessionLocal()
    try:
        if WorkflowService.is_system_paused(db):
            logger.warning(f"Kill Switch active. Halting workflow for email {email_id}.")
            return

        email_record = db.query(ProcessedEmail).filter(ProcessedEmail.id == email_id).first()
        if not email_record:
            return

        WorkflowService.transition_state(db, email_record, "PARSED")
        execute_cta_task.delay(email_id, plain_body, html_body)

    except Exception as e:
        logger.error(f"Error in process_email_workflow_task for email {email_id}: {e}")
    finally:
        db.close()
