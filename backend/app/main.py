import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, SystemSettings, ReplyTemplate
from app.security import hash_password
from app.api import auth, accounts, emails, settings as settings_api, dashboard, system

# Auto-create database tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"DB Metadata init note: {e}")

# Seed default admin & initial system settings
db = SessionLocal()
try:
    if not db.query(User).first():
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            is_admin=True
        )
        db.add(admin)

    if not db.query(SystemSettings).first():
        sys_set = SystemSettings(
            is_paused=False,
            max_concurrent_workers=5,
            min_reply_delay=30,
            max_reply_delay=180,
            cta_selector="a.cta-button",
            allowed_cta_domains="test.example.com,landing.arrowmail.internal",
            allowed_sender_domains="example.com,greenarrow.internal,arrowmail.internal"
        )
        db.add(sys_set)

    if not db.query(ReplyTemplate).first():
        tmpl1 = ReplyTemplate(name="Standard Thank You", body="Thanks, received it.", is_active=True)
        tmpl2 = ReplyTemplate(name="Review Notice", body="I'll check this and get back to you.", is_active=True)
        tmpl3 = ReplyTemplate(name="General Acknowledgment", body="Thanks for sharing this.", is_active=True)
        db.add_all([tmpl1, tmpl2, tmpl3])

    db.commit()
except Exception as e:
    db.rollback()
    print(f"Seed initialization note: {e}")
finally:
    db.close()

app = FastAPI(title=settings.APP_NAME)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(emails.router)
app.include_router(settings_api.router)
app.include_router(dashboard.router)
app.include_router(system.router)
