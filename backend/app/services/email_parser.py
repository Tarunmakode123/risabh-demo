import email
import email.utils
from email.header import decode_header
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("email_automation.parser")

@dataclass
class ExtractedLink:
    anchor_text: str
    url: str

@dataclass
class ParsedEmailData:
    message_id: str
    thread_id: Optional[str]
    sender: str
    recipient: str
    subject: str
    date_str: str
    plain_body: str
    html_body: str
    links: List[ExtractedLink]
    in_reply_to: Optional[str]
    references_header: Optional[str]
    parsed_date: Optional[datetime] = None

class EmailParserService:
    @staticmethod
    def decode_mime_words(header_val: Optional[str]) -> str:
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
        return result.strip()

    @classmethod
    def parse_raw_mime(cls, raw_bytes: bytes, fallback_recipient: str = "") -> ParsedEmailData:
        msg = email.message_from_bytes(raw_bytes)

        message_id = msg.get("Message-ID", "").strip("< >")
        in_reply_to = msg.get("In-Reply-To", "").strip("< >")
        references_header = msg.get("References", "").strip()
        thread_id = msg.get("Thread-Topic") or msg.get("Thread-Index") or message_id

        subject = cls.decode_mime_words(msg.get("Subject"))
        from_hdr = cls.decode_mime_words(msg.get("From"))
        to_hdr = cls.decode_mime_words(msg.get("To")) or fallback_recipient
        date_str = cls.decode_mime_words(msg.get("Date"))

        parsed_date = None
        if date_str:
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_str)
            except Exception:
                pass

        _, sender = email.utils.parseaddr(from_hdr)
        _, recipient = email.utils.parseaddr(to_hdr)
        if not recipient:
            recipient = fallback_recipient

        plain_body = ""
        html_body = ""

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
                                plain_body += text
                    except Exception as e:
                        logger.warning(f"Error reading MIME payload: {e}")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_body = text
                else:
                    plain_body = text

        # Safely extract hyperlinks from HTML
        extracted_links: List[ExtractedLink] = []
        if html_body:
            soup = BeautifulSoup(html_body, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                anchor = a_tag.get_text().strip()
                if href:
                    extracted_links.append(ExtractedLink(anchor_text=anchor, url=href))

        return ParsedEmailData(
            message_id=message_id,
            thread_id=thread_id,
            sender=sender,
            recipient=recipient,
            subject=subject,
            date_str=date_str,
            plain_body=plain_body,
            html_body=html_body,
            links=extracted_links,
            in_reply_to=in_reply_to,
            references_header=references_header,
            parsed_date=parsed_date
        )
