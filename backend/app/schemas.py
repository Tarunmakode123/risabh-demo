from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    class Config:
        from_attributes = True


# Inbox Account Schemas
class InboxAccountCreate(BaseModel):
    email: str
    imap_host: str
    imap_port: int = 993
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    use_ssl: bool = True
    folder: str = "INBOX"

class InboxAccountOut(BaseModel):
    id: int
    email: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    username: str
    use_ssl: bool
    folder: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# Processed Email Schemas
class ProcessedEmailOut(BaseModel):
    id: int
    correlation_id: str
    account_id: int
    message_id: str
    thread_id: Optional[str]
    sender: str
    recipient: str
    subject: Optional[str]
    campaign_id: Optional[str]
    status: str
    received_at: Optional[datetime]
    opened_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# CTA Log Schema
class CTALogOut(BaseModel):
    id: int
    email_id: int
    url: str
    is_approved: bool
    final_url: Optional[str]
    http_status: Optional[int]
    page_title: Optional[str]
    screenshot_path: Optional[str]
    execution_time_ms: Optional[int]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


# Reply Log Schema
class ReplyLogOut(BaseModel):
    id: int
    email_id: int
    in_reply_to: Optional[str]
    reply_body: str
    delay_seconds: int
    sent_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    class Config:
        from_attributes = True


# Reply Template Schemas
class ReplyTemplateCreate(BaseModel):
    name: str
    body: str

class ReplyTemplateOut(ReplyTemplateCreate):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# System Settings Schemas
class SystemSettingsUpdate(BaseModel):
    is_paused: Optional[bool] = None
    max_concurrent_workers: Optional[int] = None
    min_reply_delay: Optional[int] = None
    max_reply_delay: Optional[int] = None
    cta_selector: Optional[str] = None
    allowed_cta_domains: Optional[str] = None
    allowed_sender_domains: Optional[str] = None

class SystemSettingsOut(BaseModel):
    id: int
    is_paused: bool
    max_concurrent_workers: int
    min_reply_delay: int
    max_reply_delay: int
    cta_selector: Optional[str]
    allowed_cta_domains: Optional[str]
    allowed_sender_domains: Optional[str]
    updated_at: datetime
    class Config:
        from_attributes = True
