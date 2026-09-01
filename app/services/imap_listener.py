import imaplib
import email
from email.header import decode_header
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger("warmup.imap")

@dataclass
class ReceivedEmail:
    uid: str
    message_id: str
    subject: str
    sender_email: str
    sender_name: str
    html_body: str
    text_body: str
    folder: str
    was_spam: bool = False

class IMAPService:
    def __init__(self, host: str, port: int, email_address: str, password: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.email_address = email_address
        self.password = password
        self.use_ssl = use_ssl

    def connect(self) -> imaplib.IMAP4:
        if self.use_ssl:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            mail = imaplib.IMAP4(self.host, self.port)
        mail.login(self.email_address, self.password)
        return mail

    def test_connection(self) -> tuple[bool, str]:
        try:
            mail = self.connect()
            mail.logout()
            return True, "IMAP Connection Successful"
        except Exception as e:
            return False, f"IMAP Connection Failed: {str(e)}"

    def decode_mime_words(self, header_val: Optional[str]) -> str:
        if not header_val:
            return ""
        decoded_list = decode_header(header_val)
        result = ""
        for bytes_or_str, encoding in decoded_list:
            if isinstance(bytes_or_str, bytes):
                try:
                    result += bytes_or_str.decode(encoding or "utf-8", errors="replace")
                except Exception:
                    result += bytes_or_str.decode("latin1", errors="replace")
            else:
                result += str(bytes_or_str)
        return result

    def parse_email_message(self, raw_email: bytes, uid: str, folder: str, was_spam: bool = False) -> ReceivedEmail:
        msg = email.message_from_bytes(raw_email)
        
        subject = self.decode_mime_words(msg.get("Subject"))
        from_hdr = self.decode_mime_words(msg.get("From"))
        message_id = msg.get("Message-ID", "")
        
        sender_name, sender_email = email.utils.parseaddr(from_hdr)
        
        html_body = ""
        text_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            text = payload.decode(charset, errors="replace")
                            if content_type == "text/html":
                                html_body += text
                            elif content_type == "text/plain":
                                text_body += text
                    except Exception as e:
                        logger.warning(f"Error parsing MIME part: {e}")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_body = text
                else:
                    text_body = text

        return ReceivedEmail(
            uid=uid,
            message_id=message_id,
            subject=subject,
            sender_email=sender_email,
            sender_name=sender_name,
            html_body=html_body,
            text_body=text_body,
            folder=folder,
            was_spam=was_spam
        )

    def fetch_unseen_emails(self, sender_filter: str = "", rescue_spam: bool = True) -> List[ReceivedEmail]:
        emails: List[ReceivedEmail] = []
        try:
            mail = self.connect()
        except Exception as e:
            logger.error(f"Failed to connect IMAP for {self.email_address}: {e}")
            return emails

        folders_to_check = [("INBOX", False)]
        
        if rescue_spam:
            # Common spam folder names across different IMAP servers (Gmail, Outlook, cPanel)
            status, folder_list = mail.list()
            spam_folder_candidates = ["[Gmail]/Spam", "Spam", "Junk", "Junk E-mail", "BULK"]
            found_spam_folders = []
            if status == "OK" and folder_list:
                for f_info in folder_list:
                    f_str = f_info.decode("utf-8", errors="ignore")
                    for cand in spam_folder_candidates:
                        if cand.lower() in f_str.lower():
                            # extract folder name
                            parts = f_str.split(' "/" ')
                            if len(parts) > 1:
                                found_spam_folders.append(parts[-1].strip('"'))
                            else:
                                found_spam_folders.append(cand)
            
            for spam_f in set(found_spam_folders):
                folders_to_check.append((spam_f, True))

        for folder_name, is_spam in folders_to_check:
            try:
                res, data = mail.select(f'"{folder_name}"', readonly=False)
                if res != "OK":
                    continue
                
                search_criteria = 'UNSEEN'
                status, uids = mail.search(None, search_criteria)
                
                if status != "OK" or not uids[0]:
                    continue

                uid_list = uids[0].split()
                # Process latest up to 10 emails per folder run
                for uid in uid_list[-10:]:
                    uid_str = uid.decode()
                    res, fetch_data = mail.fetch(uid, '(BODY.PEEK[])')
                    if res == "OK" and fetch_data and fetch_data[0]:
                        raw_email = fetch_data[0][1]
                        parsed_email = self.parse_email_message(raw_email, uid_str, folder_name, was_spam=is_spam)
                        
                        # Filter by sender if filter is specified
                        if sender_filter and sender_filter.lower() not in parsed_email.sender_email.lower():
                            continue
                        
                        # If email was in spam, rescue it by moving to INBOX
                        if is_spam:
                            try:
                                mail.copy(uid, "INBOX")
                                mail.store(uid, '+FLAGS', r'(\Deleted)')
                                mail.expunge()
                                parsed_email.was_spam = True
                                logger.info(f"Rescued email '{parsed_email.subject}' from {folder_name} to INBOX")
                            except Exception as rescue_err:
                                logger.warning(f"Could not move spam mail to INBOX: {rescue_err}")

                        # Mark message as read/seen
                        mail.store(uid, '+FLAGS', r'(\Seen)')
                        emails.append(parsed_email)

            except Exception as f_err:
                logger.debug(f"Error checking folder {folder_name}: {f_err}")

        try:
            mail.logout()
        except Exception:
            pass

        return emails
