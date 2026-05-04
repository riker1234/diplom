from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.headphones import Headphones
from app.schemas.headphones import HeadphonesResponse

router = APIRouter(prefix="/headphones", tags=["headphones"])

@router.get("/", response_model=List[HeadphonesResponse])
def list_headphones(
    construction_type: Optional[str] = None,
    connection: Optional[str] = None,
    has_microphone: Optional[bool] = None,
    noise_cancellation: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Headphones)
    if construction_type:
        query = query.filter(Headphones.construction_type == construction_type)
    if connection:
        query = query.filter(Headphones.connection_types.contains(connection))
    if has_microphone is not None:
        query = query.filter(Headphones.has_microphone == has_microphone)
    if noise_cancellation:
        query = query.filter(Headphones.noise_cancellation == noise_cancellation)
    if price_max:
        query = query.filter(Headphones.price <= price_max)
    if price_min:
        query = query.filter(Headphones.price >= price_min)
    return query.all()

@router.get("/{headphones_id}", response_model=HeadphonesResponse)
def get_headphones(headphones_id: int, db: Session = Depends(get_db)):
    hp = db.query(Headphones).filter(Headphones.id == headphones_id).first()
    if not hp:
        raise HTTPException(status_code=404, detail="Headphones not found")
    return hp
