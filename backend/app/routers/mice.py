from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.mouse import Mouse
from app.schemas.mouse import MouseResponse

router = APIRouter(prefix="/mice", tags=["mice"])

@router.get("/", response_model=List[MouseResponse])
def list_mice(
    sensor: Optional[str] = None,
    connection: Optional[str] = None,
    weight_max: Optional[float] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Mouse)
    if sensor:
        query = query.filter(Mouse.sensor == sensor)
    if connection:
        query = query.filter(Mouse.connection_types.contains(connection))
    if weight_max:
        query = query.filter(Mouse.weight_g <= weight_max)
    if price_max:
        query = query.filter(Mouse.price <= price_max)
    if price_min:
        query = query.filter(Mouse.price >= price_min)
    return query.all()

@router.get("/{mouse_id}", response_model=MouseResponse)
def get_mouse(mouse_id: int, db: Session = Depends(get_db)):
    mouse = db.query(Mouse).filter(Mouse.id == mouse_id).first()
    if not mouse:
        raise HTTPException(status_code=404, detail="Mouse not found")
    return mouse
