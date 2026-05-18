from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.parsers.ozon import (
    parse_mice, parse_keyboards, parse_monitors,
    parse_headphones, parse_microphones, parse_mousepads,
    backfill_mice, backfill_keyboards, backfill_monitors,
    backfill_headphones, backfill_microphones, backfill_mousepads,
)
from app.parsers.dns import (
    parse_mice_dns, parse_keyboards_dns, parse_monitors_dns,
    parse_headphones_dns, parse_microphones_dns, parse_mousepads_dns,
)
from app.parsers.citilink import (
    parse_mice as parse_mice_citilink,
    parse_keyboards as parse_keyboards_citilink,
    parse_monitors as parse_monitors_citilink,
    parse_headphones as parse_headphones_citilink,
    parse_microphones as parse_microphones_citilink,
    parse_mousepads as parse_mousepads_citilink,
)
from app.parsers.wildberries import (
    parse_mice as parse_mice_wb,
    parse_keyboards as parse_keyboards_wb,
    parse_monitors as parse_monitors_wb,
    parse_headphones as parse_headphones_wb,
    parse_microphones as parse_microphones_wb,
    parse_mousepads as parse_mousepads_wb,
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


@router.post("/parse/mice/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_mice_wb(db: Session = Depends(get_db)):
    return parse_mice_wb(db)


@router.post("/parse/keyboards/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_keyboards_wb(db: Session = Depends(get_db)):
    return parse_keyboards_wb(db)


@router.post("/parse/monitors/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_monitors_wb(db: Session = Depends(get_db)):
    return parse_monitors_wb(db)


@router.post("/parse/headphones/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_headphones_wb(db: Session = Depends(get_db)):
    return parse_headphones_wb(db)


@router.post("/parse/microphones/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_microphones_wb(db: Session = Depends(get_db)):
    return parse_microphones_wb(db)


@router.post("/parse/mousepads/wb", dependencies=[Depends(_require_admin)])
def trigger_parse_mousepads_wb(db: Session = Depends(get_db)):
    return parse_mousepads_wb(db)


@router.post("/parse/mice/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_mice_dns(db: Session = Depends(get_db)):
    return parse_mice_dns(db)


@router.post("/parse/keyboards/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_keyboards_dns(db: Session = Depends(get_db)):
    return parse_keyboards_dns(db)


@router.post("/parse/monitors/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_monitors_dns(db: Session = Depends(get_db)):
    return parse_monitors_dns(db)


@router.post("/parse/headphones/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_headphones_dns(db: Session = Depends(get_db)):
    return parse_headphones_dns(db)


@router.post("/parse/microphones/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_microphones_dns(db: Session = Depends(get_db)):
    return parse_microphones_dns(db)


@router.post("/parse/mousepads/dns", dependencies=[Depends(_require_admin)])
def trigger_parse_mousepads_dns(db: Session = Depends(get_db)):
    return parse_mousepads_dns(db)


@router.post("/parse/mice/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_mice_citilink(db: Session = Depends(get_db)):
    return parse_mice_citilink(db)


@router.post("/parse/keyboards/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_keyboards_citilink(db: Session = Depends(get_db)):
    return parse_keyboards_citilink(db)


@router.post("/parse/monitors/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_monitors_citilink(db: Session = Depends(get_db)):
    return parse_monitors_citilink(db)


@router.post("/parse/headphones/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_headphones_citilink(db: Session = Depends(get_db)):
    return parse_headphones_citilink(db)


@router.post("/parse/microphones/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_microphones_citilink(db: Session = Depends(get_db)):
    return parse_microphones_citilink(db)


@router.post("/parse/mousepads/citilink", dependencies=[Depends(_require_admin)])
def trigger_parse_mousepads_citilink(db: Session = Depends(get_db)):
    return parse_mousepads_citilink(db)


@router.post("/backfill/mice", dependencies=[Depends(_require_admin)])
def trigger_backfill_mice(db: Session = Depends(get_db)):
    return backfill_mice(db)


@router.post("/backfill/keyboards", dependencies=[Depends(_require_admin)])
def trigger_backfill_keyboards(db: Session = Depends(get_db)):
    return backfill_keyboards(db)


@router.post("/backfill/monitors", dependencies=[Depends(_require_admin)])
def trigger_backfill_monitors(db: Session = Depends(get_db)):
    return backfill_monitors(db)


@router.post("/backfill/headphones", dependencies=[Depends(_require_admin)])
def trigger_backfill_headphones(db: Session = Depends(get_db)):
    return backfill_headphones(db)


@router.post("/backfill/microphones", dependencies=[Depends(_require_admin)])
def trigger_backfill_microphones(db: Session = Depends(get_db)):
    return backfill_microphones(db)


@router.post("/backfill/mousepads", dependencies=[Depends(_require_admin)])
def trigger_backfill_mousepads(db: Session = Depends(get_db)):
    return backfill_mousepads(db)
