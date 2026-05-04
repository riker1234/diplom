from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.monitor import Monitor
from app.schemas.monitor import MonitorResponse

router = APIRouter(prefix="/monitors", tags=["monitors"])

@router.get("/", response_model=List[MonitorResponse])
def list_monitors(
    diagonal_min: Optional[float] = None,
    diagonal_max: Optional[float] = None,
    resolution: Optional[str] = None,
    refresh_rate_min: Optional[int] = None,
    matrix_type: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Monitor)
    if diagonal_min:
        query = query.filter(Monitor.diagonal_inch >= diagonal_min)
    if diagonal_max:
        query = query.filter(Monitor.diagonal_inch <= diagonal_max)
    if resolution:
        query = query.filter(Monitor.resolution == resolution)
    if refresh_rate_min:
        query = query.filter(Monitor.refresh_rate_hz >= refresh_rate_min)
    if matrix_type:
        query = query.filter(Monitor.matrix_type == matrix_type)
    if price_max:
        query = query.filter(Monitor.price <= price_max)
    if price_min:
        query = query.filter(Monitor.price >= price_min)
    return query.all()

@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db)):
    mon = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return mon
