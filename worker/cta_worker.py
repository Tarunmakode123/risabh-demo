import asyncio
import logging
from celery_app import celery_app
from app.database import SessionLocal
from app.models import ProcessedEmail, CTALog, SystemSettings
from app.services.cta_service import CTAService
from app.services.deduplication import DeduplicationService
from app.services.workflow_service import WorkflowService
from worker.playwright_engine import PlaywrightEngine

logger = logging.getLogger("email_automation.cta_worker")

@celery_app.task(name="worker.cta_worker.execute_cta_task")
def execute_cta_task(email_id: int, plain_body: str = "", html_body: str = ""):
    db = SessionLocal()
    try:
        # Pre-action check: Kill Switch
        if WorkflowService.is_system_paused(db):
            logger.warning(f"Kill Switch active. Pausing CTA task for email {email_id}.")
            return

        # Atomic State Acquisition
        email_record = DeduplicationService.acquire_email_atomically(db, email_id)
        if not email_record:
            logger.warning(f"Could not acquire atomic lock for email_id {email_id}. Skipping.")
            return

        settings_rec = db.query(SystemSettings).first()
        cta_selector = settings_rec.cta_selector if settings_rec else "a.cta-button"
        allowed_domains_str = settings_rec.allowed_cta_domains if settings_rec else ""
        allowed_domains = [d.strip() for d in allowed_domains_str.split(",") if d.strip()] if allowed_domains_str else None

        # Extract & Validate Candidate CTA URL
        candidate_url, cta_status = CTAService.extract_and_validate_cta(
            html_body=html_body,
            plain_body=plain_body,
            cta_selector=cta_selector,
            allowed_domains=allowed_domains
        )

        if not candidate_url:
            WorkflowService.transition_state(db, email_record, cta_status, error_msg="No valid approved CTA found")
            return

        WorkflowService.transition_state(db, email_record, "CTA_VALIDATED")

        # Run Playwright Browser Execution
        loop = asyncio.get_event_loop()
        playwright_result = loop.run_until_complete(
            PlaywrightEngine.execute_cta_visit(candidate_url, email_id, allowed_domains)
        )

        # Log CTA Result
        db.add(CTALog(
            email_id=email_id,
            url=candidate_url,
            is_approved=True,
            final_url=playwright_result.final_url,
            http_status=playwright_result.http_status,
            page_title=playwright_result.page_title,
            screenshot_path=playwright_result.screenshot_path,
            execution_time_ms=playwright_result.execution_time_ms,
            status=playwright_result.status_text
        ))
        db.commit()

        if playwright_result.success:
            WorkflowService.transition_state(db, email_record, "CTA_CLICKED")
            # Queue Reply Task
            from worker.reply_worker import execute_reply_task
            execute_reply_task.delay(email_id)
        else:
            WorkflowService.transition_state(db, email_record, "CTA_BLOCKED", error_msg=playwright_result.status_text)

    except Exception as e:
        logger.error(f"Error executing CTA task for email {email_id}: {e}")
        email_record = db.query(ProcessedEmail).filter(ProcessedEmail.id == email_id).first()
        if email_record:
            WorkflowService.transition_state(db, email_record, "ERROR", error_msg=str(e))
    finally:
        db.close()
