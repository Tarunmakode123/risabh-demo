import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "IP Warmup Automation System"
    DATABASE_URL: str = "sqlite:////tmp/warmup.db" if os.environ.get("VERCEL") else "sqlite:///./warmup.db"
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
