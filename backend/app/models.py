import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InboxAccount(Base):
    __tablename__ = "inbox_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    imap_host = Column(String, nullable=False)
    imap_port = Column(Integer, default=993)
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(Integer, default=587)
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)
    use_ssl = Column(Boolean, default=True)
    folder = Column(String, default="INBOX")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    emails = relationship("ProcessedEmail", back_populates="account", cascade="all, delete-orphan")


class ProcessedEmail(Base):
    __tablename__ = "processed_emails"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String, default=lambda: str(uuid.uuid4()), index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("inbox_accounts.id"), nullable=False)
    message_id = Column(String, index=True, nullable=False)
    thread_id = Column(String, nullable=True)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    campaign_id = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    status = Column(String, default="DETECTED", index=True)  # State Machine State
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("account_id", "message_id", name="uq_account_message_id"),
    )

    account = relationship("InboxAccount", back_populates="emails")
    links = relationship("EmailLink", back_populates="email", cascade="all, delete-orphan")
    cta_logs = relationship("CTALog", back_populates="email", cascade="all, delete-orphan")
    reply_logs = relationship("ReplyLog", back_populates="email", cascade="all, delete-orphan")


class EmailLink(Base):
    __tablename__ = "email_links"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("processed_emails.id"), nullable=False)
    anchor_text = Column(String, nullable=True)
    url = Column(Text, nullable=False)
    is_cta_candidate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("ProcessedEmail", back_populates="links")


class CTALog(Base):
    __tablename__ = "cta_logs"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("processed_emails.id"), nullable=False)
    url = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    final_url = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    page_title = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String, default="PENDING")  # SUCCESS, BLOCKED_REDIRECT, TIMEOUT, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("ProcessedEmail", back_populates="cta_logs")


class ReplyLog(Base):
    __tablename__ = "reply_logs"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("processed_emails.id"), nullable=False)
    in_reply_to = Column(String, nullable=True)
    references_header = Column(String, nullable=True)
    reply_body = Column(Text, nullable=False)
    delay_seconds = Column(Integer, default=0)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, default="QUEUED")  # QUEUED, SENT, FAILED
    error_message = Column(Text, nullable=True)

    email = relationship("ProcessedEmail", back_populates="reply_logs")


class ReplyTemplate(Base):
    __tablename__ = "reply_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    is_paused = Column(Boolean, default=False)
    max_concurrent_workers = Column(Integer, default=5)
    min_reply_delay = Column(Integer, default=30)
    max_reply_delay = Column(Integer, default=180)
    cta_selector = Column(String, nullable=True, default="a.cta-button")
    allowed_cta_domains = Column(Text, nullable=True, default="test.example.com,landing.arrowmail.internal")
    allowed_sender_domains = Column(Text, nullable=True, default="example.com,greenarrow.internal,arrowmail.internal")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
