from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.mousepad import Mousepad
from app.schemas.mousepad import MousepadResponse

router = APIRouter(prefix="/mousepads", tags=["mousepads"])

@router.get("/", response_model=List[MousepadResponse])
def list_mousepads(
    size: Optional[str] = None,
    surface_material: Optional[str] = None,
    hardness: Optional[str] = None,
    has_rgb: Optional[bool] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Mousepad)
    if size:
        query = query.filter(Mousepad.size == size)
    if surface_material:
        query = query.filter(Mousepad.surface_material == surface_material)
    if hardness:
        query = query.filter(Mousepad.hardness == hardness)
    if has_rgb is not None:
        query = query.filter(Mousepad.has_rgb == has_rgb)
    if price_max:
        query = query.filter(Mousepad.price <= price_max)
    if price_min:
        query = query.filter(Mousepad.price >= price_min)
    return query.all()

@router.get("/{pad_id}", response_model=MousepadResponse)
def get_mousepad(pad_id: int, db: Session = Depends(get_db)):
    pad = db.query(Mousepad).filter(Mousepad.id == pad_id).first()
    if not pad:
        raise HTTPException(status_code=404, detail="Mousepad not found")
    return pad
