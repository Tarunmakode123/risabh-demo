import smtplib
import logging
from typing import Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("email_automation.smtp")

class SMTPService:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = False
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    def connect(self) -> smtplib.SMTP:
        if self.use_ssl or self.port == 465:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
        else:
            try:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                server.ehlo()
                if server.has_extn("STARTTLS"):
                    server.starttls()
                    server.ehlo()
            except Exception as e:
                logger.info(f"Port {self.port} connection note ({e}). Falling back to SMTP_SSL port 465...")
                server = smtplib.SMTP_SSL(self.host, 465, timeout=15)

        server.login(self.username, self.password)
        return server

    def test_connection(self) -> Tuple[bool, str]:
        try:
            server = self.connect()
            server.quit()
            return True, "SMTP Connection Successful"
        except Exception as e:
            return False, f"SMTP Connection Error: {str(e)}"

    def send_threaded_reply(
        self,
        to_email: str,
        original_subject: str,
        in_reply_to: str,
        references_header: str,
        reply_body: str,
        correlation_id: str = ""
    ) -> Tuple[bool, str]:
        if not to_email:
            return False, "Recipient email address is missing"

        reply_subject = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"

        msg = MIMEMultipart("alternative")
        msg["From"] = self.username
        msg["To"] = to_email
        msg["Subject"] = reply_subject

        if in_reply_to:
            msg["In-Reply-To"] = f"<{in_reply_to.strip('< >')}>"
        if references_header:
            msg["References"] = references_header
        elif in_reply_to:
            msg["References"] = f"<{in_reply_to.strip('< >')}>"

        if correlation_id:
            msg["X-Correlation-ID"] = correlation_id

        msg.attach(MIMEText(reply_body, "plain"))

        try:
            server = self.connect()
            server.sendmail(self.username, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Successfully sent threaded reply to {to_email} (Correlation ID: {correlation_id})")
            return True, f"SMTP Reply dispatched successfully: '{reply_body[:30]}...'"
        except Exception as e:
            logger.error(f"Failed to send SMTP reply to {to_email}: {e}")
            return False, f"SMTP Send Failure: {str(e)}"
