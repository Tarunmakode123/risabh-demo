import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import auth, accounts, emails, settings as settings_api, dashboard, system

# Safely attempt database table creation without blocking startup
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"DB Metadata init note: {e}")

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
