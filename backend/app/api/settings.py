from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SystemSettings, ReplyTemplate
from app.schemas import SystemSettingsOut, SystemSettingsUpdate, ReplyTemplateCreate, ReplyTemplateOut

router = APIRouter(prefix="/api/settings", tags=["Settings & Templates"])

def get_or_create_settings(db: Session) -> SystemSettings:
    rec = db.query(SystemSettings).first()
    if not rec:
        rec = SystemSettings()
        db.add(rec)
        db.commit()
        db.refresh(rec)
    return rec

@router.get("", response_model=SystemSettingsOut)
def get_system_settings(db: Session = Depends(get_db)):
    return get_or_create_settings(db)

@router.put("", response_model=SystemSettingsOut)
def update_system_settings(payload: SystemSettingsUpdate, db: Session = Depends(get_db)):
    settings_rec = get_or_create_settings(db)
    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        if value is not None:
            setattr(settings_rec, key, value)
    db.commit()
    db.refresh(settings_rec)
    return settings_rec

# --- Reply Templates ---
@router.get("/templates", response_model=List[ReplyTemplateOut])
def list_reply_templates(db: Session = Depends(get_db)):
    return db.query(ReplyTemplate).all()

@router.post("/templates", response_model=ReplyTemplateOut)
def create_reply_template(payload: ReplyTemplateCreate, db: Session = Depends(get_db)):
    tmpl = ReplyTemplate(name=payload.name, body=payload.body, is_active=True)
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl

@router.delete("/templates/{template_id}")
def delete_reply_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(ReplyTemplate).filter(ReplyTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found.")
    db.delete(tmpl)
    db.commit()
    return {"message": "Template deleted"}
