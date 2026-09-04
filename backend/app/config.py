import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

def get_default_db_url() -> str:
    # On Vercel / serverless or read-only environments, use in-memory SQLite database
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("AWS_EXECUTION_ENV"):
        return "sqlite:///:memory:"
    try:
        test_path = "./.perm_test"
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
        return "sqlite:///./email_automation.db"
    except Exception:
        return "sqlite:///:memory:"

class Settings(BaseSettings):
    APP_NAME: str = "ArrowMail / GreenArrow Interaction Automation"
    DEBUG: bool = False
    DATABASE_URL: str = get_default_db_url()

    # Celery & Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Encryption
    JWT_SECRET: str = "supersecretjwtkey_arrowmail_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days
    ENCRYPTION_KEY: str = "supersecretfernetkey123456789012"  # Fernet key

    # Allowlists & Security Rules
    ALLOWED_SENDER_DOMAINS: str = "example.com,greenarrow.internal,arrowmail.internal,gmail.com"
    ALLOWED_RECIPIENT_DOMAINS: str = "test.example.com,internal.inbox,gmail.com"
    ALLOWED_CTA_DOMAINS: str = "test.example.com,landing.arrowmail.internal,google.com,github.com,example.com"

    # Playwright Settings
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 30000

    # System Settings
    MAX_CONCURRENT_WORKERS: int = 5
    MIN_REPLY_DELAY: int = 30
    MAX_REPLY_DELAY: int = 180

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
