import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Email Interaction Bot (ArrowMail/GreenArrow)"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./email_automation.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Security & Encryption Secrets
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-signing-key-32bytes-long")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dGhpcy1pcy1hLXNhbXBsZS1mZXJuZXQta2V5LTMyYnl0ZXM9")

    # IMAP Configuration
    IMAP_POLL_INTERVAL: int = int(os.getenv("IMAP_POLL_INTERVAL", "15"))

    # Playwright Settings
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    PLAYWRIGHT_TIMEOUT: int = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))
    SCREENSHOT_ON_SUCCESS: bool = os.getenv("SCREENSHOT_ON_SUCCESS", "false").lower() == "true"
    SCREENSHOT_ON_FAILURE: bool = os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    SCREENSHOT_DIR: str = os.getenv("SCREENSHOT_DIR", "./screenshots")

    # Auto-Reply Delays (Seconds)
    MIN_REPLY_DELAY: int = int(os.getenv("MIN_REPLY_DELAY", "30"))
    MAX_REPLY_DELAY: int = int(os.getenv("MAX_REPLY_DELAY", "180"))

    # Security Domain Allowlists
    ALLOWED_SENDER_DOMAINS_RAW: str = os.getenv("ALLOWED_SENDER_DOMAINS", "example.com,greenarrow.internal,arrowmail.internal")
    ALLOWED_RECIPIENT_DOMAINS_RAW: str = os.getenv("ALLOWED_RECIPIENT_DOMAINS", "test.example.com,internal.inbox")
    ALLOWED_CTA_DOMAINS_RAW: str = os.getenv("ALLOWED_CTA_DOMAINS", "test.example.com,landing.arrowmail.internal")

    # Worker Concurrency
    MAX_CONCURRENT_WORKERS: int = int(os.getenv("MAX_CONCURRENT_WORKERS", "5"))

    @property
    def ALLOWED_SENDER_DOMAINS(self) -> List[str]:
        return [d.strip().lower() for d in self.ALLOWED_SENDER_DOMAINS_RAW.split(",") if d.strip()]

    @property
    def ALLOWED_RECIPIENT_DOMAINS(self) -> List[str]:
        return [d.strip().lower() for d in self.ALLOWED_RECIPIENT_DOMAINS_RAW.split(",") if d.strip()]

    @property
    def ALLOWED_CTA_DOMAINS(self) -> List[str]:
        return [d.strip().lower() for d in self.ALLOWED_CTA_DOMAINS_RAW.split(",") if d.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
