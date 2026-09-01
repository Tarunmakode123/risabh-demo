import os
from pydantic_settings import BaseSettings

def get_default_db_url() -> str:
    # On Vercel / serverless or read-only environments, store DB in /tmp
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("AWS_EXECUTION_ENV"):
        return "sqlite:////tmp/warmup.db"
    try:
        test_path = "./.perm_test"
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
        return "sqlite:///./warmup.db"
    except Exception:
        return "sqlite:////tmp/warmup.db"

class Settings(BaseSettings):
    APP_NAME: str = "IP Warmup Automation System"
    DATABASE_URL: str = get_default_db_url()
    SECRET_KEY: str = "super-secret-key-change-in-production"
    
    # Worker Settings
    DEFAULT_POLL_INTERVAL_SECONDS: int = 30
    MIN_ACTION_DELAY_SECONDS: int = 5
    MAX_ACTION_DELAY_SECONDS: int = 15
    
    # User Agent for opening links & pixels
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    
    # Default Auto-Reply Templates (high-reputation positive signals)
    DEFAULT_REPLY_TEMPLATES: list[str] = [
        "Thank you for the update! I received your email and appreciate the information.",
        "Thanks for sending this over. Looks great, let's keep in touch!",
        "Got it, thank you! I'll review the details and get back to you if needed.",
        "Hi! Thanks for reaching out. Everything looks clear on my end.",
        "Appreciate the message! Have a wonderful day ahead.",
        "Received loud and clear! Thank you for keeping me posted.",
        "Thanks for the details. Hope you have a great week ahead!",
        "Great update, thanks for sharing this with me."
    ]
    
    # Optional LLM API Key (for smart reply generation if configured)
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
