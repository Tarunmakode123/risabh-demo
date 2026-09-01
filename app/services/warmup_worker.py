import asyncio
from datetime import datetime, date
import logging
import random
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.schema import SeedAccount, WarmupLog, WarmupMetric
from app.services.imap_listener import IMAPService, ReceivedEmail
from app.services.html_processor import HTMLProcessorService
from app.services.smtp_replyer import SMTPReplyService

logger = logging.getLogger("warmup.worker")

class WarmupWorker:
    def __init__(self):
        self.is_running = False
        self._task = None
        self.poll_interval = settings.DEFAULT_POLL_INTERVAL_SECONDS
        self.html_processor = HTMLProcessorService()

    def start(self, poll_interval: int = None):
        if self.is_running:
            return
        if poll_interval:
            self.poll_interval = poll_interval
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Warmup Worker started (interval: {self.poll_interval}s)")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("Warmup Worker stopped")

    async def _run_loop(self):
        while self.is_running:
            try:
                await self.process_all_accounts()
            except Exception as e:
                logger.error(f"Error in warmup worker loop: {e}", exc_info=True)

            await asyncio.sleep(self.poll_interval)

    async def process_all_accounts(self):
        db: Session = SessionLocal()
        try:
            active_accounts = db.query(SeedAccount).filter(SeedAccount.is_active == True).all()
            if not active_accounts:
                logger.debug("No active seed accounts configured.")
                return

            for account in active_accounts:
                await self.process_single_account(db, account)

        finally:
            db.close()

    async def process_single_account(self, db: Session, account: SeedAccount):
        logger.info(f"Checking seed inbox: {account.email}")
        
        imap = IMAPService(
            host=account.imap_host,
            port=account.imap_port,
            email_address=account.email,
            password=account.password,
            use_ssl=account.imap_use_ssl
        )

        unseen_emails = imap.fetch_unseen_emails(
            sender_filter=account.sender_filter or "",
            rescue_spam=account.auto_rescue_spam
        )

        account.last_checked_at = datetime.utcnow()
        db.commit()

        if not unseen_emails:
            logger.debug(f"No new warm-up emails found for {account.email}")
            return

        today_str = date.today().isoformat()
        metric = db.query(WarmupMetric).filter(WarmupMetric.date == today_str).first()
        if not metric:
            metric = WarmupMetric(date=today_str)
            db.add(metric)
            db.commit()
            db.refresh(metric)

        for mail in unseen_emails:
            # 1. SPAM RESCUE ACTION
            if mail.was_spam:
                account.total_spam_rescued += 1
                metric.spam_rescued_count += 1
                db.add(WarmupLog(
                    seed_account_id=account.id,
                    action="SPAM_RESCUE",
                    subject=mail.subject,
                    sender_email=mail.sender_email,
                    details=f"Moved email from {mail.folder} to INBOX (Not Spam flag signal)",
                    status="SUCCESS"
                ))
                db.commit()

            # 2. OPEN & PIXEL LOAD ACTION
            pixel_count = await self.html_processor.load_tracking_pixels(mail.html_body)
            account.total_opened += 1
            metric.opened_count += 1
            db.add(WarmupLog(
                seed_account_id=account.id,
                action="OPEN",
                subject=mail.subject,
                sender_email=mail.sender_email,
                details=f"Opened email and loaded {pixel_count} tracking image(s)/pixel(s)",
                status="SUCCESS"
            ))
            db.commit()

            # Human Delay
            delay = random.randint(settings.MIN_ACTION_DELAY_SECONDS, settings.MAX_ACTION_DELAY_SECONDS)
            await asyncio.sleep(delay)

            # 3. CTA CLICK ACTION
            if account.auto_click_cta:
                cta_links = self.html_processor.extract_cta_links(mail.html_body)
                if cta_links:
                    success, target_url, msg = await self.html_processor.click_cta_link(cta_links)
                    if success:
                        account.total_clicked += 1
                        metric.clicked_count += 1
                    db.add(WarmupLog(
                        seed_account_id=account.id,
                        action="CLICK",
                        subject=mail.subject,
                        sender_email=mail.sender_email,
                        details=f"{msg} | URL: {target_url}",
                        status="SUCCESS" if success else "WARNING"
                    ))
                    db.commit()
                else:
                    logger.debug("No CTA links found in email HTML")

            # Human Delay before reply
            delay = random.randint(settings.MIN_ACTION_DELAY_SECONDS, settings.MAX_ACTION_DELAY_SECONDS)
            await asyncio.sleep(delay)

            # 4. AUTO REPLY ACTION
            if account.auto_reply:
                smtp = SMTPReplyService(
                    host=account.smtp_host,
                    port=account.smtp_port,
                    email_address=account.email,
                    password=account.password,
                    display_name=account.display_name,
                    use_ssl=account.smtp_use_ssl
                )
                
                success, reply_msg = smtp.send_reply(
                    to_email=mail.sender_email,
                    original_subject=mail.subject,
                    original_message_id=mail.message_id
                )

                if success:
                    account.total_replied += 1
                    metric.replied_count += 1

                db.add(WarmupLog(
                    seed_account_id=account.id,
                    action="REPLY",
                    subject=mail.subject,
                    sender_email=mail.sender_email,
                    details=reply_msg,
                    status="SUCCESS" if success else "FAILED"
                ))
                db.commit()

# Singleton worker instance
warmup_worker = WarmupWorker()
