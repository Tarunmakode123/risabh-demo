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

    def rescue_spam_emails(self, mail: imaplib.IMAP4, limit: int = 10) -> List[ParsedEmailData]:
        """
        Scans Spam/Junk folders. If an email is found in Spam/Junk, moves it to INBOX
        (rescuing deliverability reputation) and returns it for immediate processing.
        """
        rescued: List[ParsedEmailData] = []
        spam_folders = ["[Gmail]/Spam", "Spam", "Junk", "Junk E-mail", "INBOX.Spam", "INBOX.Junk"]

        for spam_folder in spam_folders:
            try:
                res, _ = mail.select(f'"{spam_folder}"', readonly=False)
                if res != "OK":
                    continue

                res, data = mail.search(None, "ALL")
                if res != "OK" or not data[0]:
                    continue

                uids = data[0].split()
                logger.info(f"Found {len(uids)} email(s) in SPAM folder '{spam_folder}'. Auto-moving to INBOX...")

                for uid in uids[-limit:]:
                    res, msg_data = mail.fetch(uid, '(BODY.PEEK[])')
                    if res == "OK" and msg_data and msg_data[0]:
                        raw_mime = msg_data[0][1]
                        parsed = EmailParserService.parse_raw_mime(raw_mime, fallback_recipient=self.username)
                        
                        # Copy email to INBOX
                        copy_res, _ = mail.copy(uid, "INBOX")
                        if copy_res == "OK":
                            # Delete from Spam folder
                            mail.store(uid, "+FLAGS", "\\Deleted")
                            mail.expunge()
                            logger.info(f"Successfully moved email '{parsed.subject}' from '{spam_folder}' to INBOX!")
                            rescued.append(parsed)
            except Exception as e:
                logger.debug(f"Spam scan note for folder '{spam_folder}': {e}")

        return rescued

    def fetch_new_messages(self, limit: int = 30) -> List[ParsedEmailData]:
        parsed_emails: List[ParsedEmailData] = []
        try:
            mail = self.connect()

            # First: Auto-rescue emails sitting in Spam / Junk folders
            spam_rescued = self.rescue_spam_emails(mail, limit=limit)
            parsed_emails.extend(spam_rescued)

            # Second: Fetch messages from target INBOX
            res, _ = mail.select(f'"{self.folder}"', readonly=False)
            if res == "OK":
                res, data = mail.search(None, 'ALL')
                if res == "OK" and data[0]:
                    uids = data[0].split()
                    for uid in uids[-limit:]:
                        res, msg_data = mail.fetch(uid, '(BODY.PEEK[])')
                        if res == "OK" and msg_data and msg_data[0]:
                            raw_mime = msg_data[0][1]
                            parsed = EmailParserService.parse_raw_mime(raw_mime, fallback_recipient=self.username)
                            parsed_emails.append(parsed)

            mail.logout()
        except Exception as e:
            logger.error(f"IMAP Fetch Error for {self.username}: {e}")

        return parsed_emails
