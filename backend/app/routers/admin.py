from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.parsers.wildberries import (
    parse_mice,
    parse_keyboards,
    parse_monitors,
    parse_headphones,
    parse_microphones,
    parse_mousepads,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/parse/mice", dependencies=[Depends(_require_admin)])
def trigger_parse_mice(db: Session = Depends(get_db)):
    return parse_mice(db)


@router.post("/parse/keyboards", dependencies=[Depends(_require_admin)])
def trigger_parse_keyboards(db: Session = Depends(get_db)):
    return parse_keyboards(db)


@router.post("/parse/monitors", dependencies=[Depends(_require_admin)])
def trigger_parse_monitors(db: Session = Depends(get_db)):
    return parse_monitors(db)


@router.post("/parse/headphones", dependencies=[Depends(_require_admin)])
def trigger_parse_headphones(db: Session = Depends(get_db)):
    return parse_headphones(db)


@router.post("/parse/microphones", dependencies=[Depends(_require_admin)])
def trigger_parse_microphones(db: Session = Depends(get_db)):
    return parse_microphones(db)


@router.post("/parse/mousepads", dependencies=[Depends(_require_admin)])
def trigger_parse_mousepads(db: Session = Depends(get_db)):
    return parse_mousepads(db)
