from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SeedAccount(Base):
    __tablename__ = "seed_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    
    # IMAP Configuration
    imap_host = Column(String, nullable=False)
    imap_port = Column(Integer, default=993)
    imap_use_ssl = Column(Boolean, default=True)
    
    # SMTP Configuration
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_use_ssl = Column(Boolean, default=False)
    
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Filter incoming mail by sender domain or email address (optional)
    sender_filter = Column(String, nullable=True, default="")
    
    # Enable specific features
    auto_rescue_spam = Column(Boolean, default=True)
    auto_click_cta = Column(Boolean, default=True)
    auto_reply = Column(Boolean, default=True)
    
    # Cumulative Stats
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_replied = Column(Integer, default=0)
    total_spam_rescued = Column(Integer, default=0)
    
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("WarmupLog", back_populates="seed_account", cascade="all, delete-orphan")


class WarmupLog(Base):
    __tablename__ = "warmup_logs"

    id = Column(Integer, primary_key=True, index=True)
    seed_account_id = Column(Integer, ForeignKey("seed_accounts.id"), nullable=False)
    action = Column(String, nullable=False)  # SPAM_RESCUE, OPEN, CLICK, REPLY, ERROR
    subject = Column(String, nullable=True)
    sender_email = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    status = Column(String, default="SUCCESS")  # SUCCESS, WARNING, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    seed_account = relationship("SeedAccount", back_populates="logs")


class WarmupMetric(Base):
    __tablename__ = "warmup_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True, nullable=False, unique=True)  # YYYY-MM-DD
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    spam_rescued_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
