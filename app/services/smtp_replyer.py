import smtplib
import random
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger("warmup.smtp")

class SMTPReplyService:
    def __init__(
        self, 
        host: str, 
        port: int, 
        email_address: str, 
        password: str, 
        display_name: str = "",
        use_ssl: bool = False
    ):
        self.host = host
        self.port = port
        self.email_address = email_address
        self.password = password
        self.display_name = display_name or email_address.split("@")[0]
        self.use_ssl = use_ssl

    def connect(self) -> smtplib.SMTP:
        if self.use_ssl or self.port == 465:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=15)
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls()
                server.ehlo()

        server.login(self.email_address, self.password)
        return server

    def test_connection(self) -> tuple[bool, str]:
        try:
            server = self.connect()
            server.quit()
            return True, "SMTP Connection Successful"
        except Exception as e:
            return False, f"SMTP Connection Failed: {str(e)}"

    def generate_reply_text(self, original_text: str = "") -> str:
        """Pick a high-reputation reply template."""
        templates = settings.DEFAULT_REPLY_TEMPLATES
        return random.choice(templates)

    def send_reply(
        self, 
        to_email: str, 
        original_subject: str, 
        original_message_id: str = "",
        custom_reply_text: str = ""
    ) -> tuple[bool, str]:
        if not to_email:
            return False, "Target reply email address is missing"

        reply_subject = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"
        reply_body = custom_reply_text or self.generate_reply_text()

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.display_name} <{self.email_address}>"
        msg["To"] = to_email
        msg["Subject"] = reply_subject

        if original_message_id:
            msg["In-Reply-To"] = original_message_id
            msg["References"] = original_message_id

        msg.attach(MIMEText(reply_body, "plain"))

        try:
            server = self.connect()
            server.sendmail(self.email_address, [to_email], msg.as_string())
            server.quit()
            logger.info(f"Successfully sent warm-up reply to {to_email}")
            return True, f"Sent reply: '{reply_body[:40]}...'"
        except Exception as e:
            logger.error(f"Failed to send reply to {to_email}: {e}")
            return False, f"SMTP Send Error: {str(e)}"
