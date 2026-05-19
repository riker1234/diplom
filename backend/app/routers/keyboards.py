from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.keyboard import Keyboard
from app.schemas.keyboard import KeyboardResponse

router = APIRouter(prefix="/keyboards", tags=["keyboards"])

@router.get("/", response_model=List[KeyboardResponse])
def list_keyboards(
    switches: Optional[str] = None,
    form_factor: Optional[str] = None,
    connection: Optional[str] = None,
    keycap_material: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Keyboard)
    if switches:
        query = query.filter(Keyboard.switches.contains(switches))
    if form_factor:
        query = query.filter(Keyboard.form_factor == form_factor)
    if connection:
        query = query.filter(Keyboard.connection_types.contains(connection))
    if keycap_material:
        query = query.filter(Keyboard.keycap_material == keycap_material)
    if price_max:
        query = query.filter(or_(
            Keyboard.price <= price_max,
            Keyboard.wb_price <= price_max,
            Keyboard.citilink_price <= price_max,
        ))
    if price_min:
        query = query.filter(
            or_(Keyboard.price == None, Keyboard.price >= price_min),
            or_(Keyboard.wb_price == None, Keyboard.wb_price >= price_min),
            or_(Keyboard.citilink_price == None, Keyboard.citilink_price >= price_min),
        )
    return query.all()

@router.get("/{keyboard_id}", response_model=KeyboardResponse)
def get_keyboard(keyboard_id: int, db: Session = Depends(get_db)):
    kb = db.query(Keyboard).filter(Keyboard.id == keyboard_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Keyboard not found")
    return kb
