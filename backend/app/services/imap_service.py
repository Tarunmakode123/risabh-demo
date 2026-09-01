import imaplib
import logging
from typing import List, Tuple, Optional
from app.services.email_parser import EmailParserService, ParsedEmailData

logger = logging.getLogger("email_automation.imap")

class IMAPService:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        folder: str = "INBOX"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.folder = folder

    def connect(self) -> imaplib.IMAP4:
        if self.use_ssl or self.port == 993:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            mail = imaplib.IMAP4(self.host, self.port)
        mail.login(self.username, self.password)
        return mail

    def test_connection(self) -> Tuple[bool, str]:
        try:
            mail = self.connect()
            mail.logout()
            return True, "IMAP Connection Successful"
        except Exception as e:
            return False, f"IMAP Connection Error: {str(e)}"

    def fetch_new_messages(self, limit: int = 15) -> List[ParsedEmailData]:
        parsed_emails: List[ParsedEmailData] = []
        try:
            mail = self.connect()
            res, _ = mail.select(f'"{self.folder}"', readonly=False)
            if res != "OK":
                logger.error(f"Could not select folder {self.folder} on IMAP server")
                mail.logout()
                return []

            res, data = mail.search(None, 'UNSEEN')
            if res != "OK" or not data[0]:
                mail.logout()
                return []

            uids = data[0].split()
            for uid in uids[-limit:]:
                res, msg_data = mail.fetch(uid, '(BODY.PEEK[])')
                if res == "OK" and msg_data and msg_data[0]:
                    raw_mime = msg_data[0][1]
                    parsed = EmailParserService.parse_raw_mime(raw_mime, fallback_recipient=self.username)
                    parsed_emails.append(parsed)
                    
                    # Mark as seen
                    mail.store(uid, '+FLAGS', r'(\Seen)')

            mail.logout()
        except Exception as e:
            logger.error(f"IMAP Fetch Error for {self.username}: {e}")

        return parsed_emails
