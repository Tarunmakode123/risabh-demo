from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import SystemSettings
from app.api.settings import get_or_create_settings
from app.config import settings

router = APIRouter(tags=["System & Health"])

@router.get("/api/system/status")
def get_system_status(db: Session = Depends(get_db)):
    settings_rec = get_or_create_settings(db)
    return {
        "is_paused": settings_rec.is_paused,
        "max_concurrent_workers": settings_rec.max_concurrent_workers,
        "min_reply_delay": settings_rec.min_reply_delay,
        "max_reply_delay": settings_rec.max_reply_delay,
        "cta_selector": settings_rec.cta_selector,
        "allowed_cta_domains": settings_rec.allowed_cta_domains,
        "allowed_sender_domains": settings_rec.allowed_sender_domains
    }

@router.post("/api/system/pause")
def pause_system(db: Session = Depends(get_db)):
    settings_rec = get_or_create_settings(db)
    settings_rec.is_paused = True
    db.commit()
    return {"message": "ALL AUTOMATION PAUSED (Kill Switch Active)", "is_paused": True}

@router.post("/api/system/resume")
def resume_system(db: Session = Depends(get_db)):
    settings_rec = get_or_create_settings(db)
    settings_rec.is_paused = False
    db.commit()
    return {"message": "AUTOMATION RESUMED", "is_paused": False}

# --- Mandatory Health Checks ---
@router.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@router.get("/health/database")
def health_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "PostgreSQL Connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Health Failed: {str(e)}")

@router.get("/health/redis")
def health_redis():
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=3)
        r.ping()
        return {"status": "ok", "redis": "Redis Connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis Health Failed: {str(e)}")

@router.get("/health/workers")
def health_workers(db: Session = Depends(get_db)):
    settings_rec = get_or_create_settings(db)
    return {
        "status": "ok" if not settings_rec.is_paused else "paused",
        "is_paused": settings_rec.is_paused,
        "max_concurrent_workers": settings_rec.max_concurrent_workers
    }
