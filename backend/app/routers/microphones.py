from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.microphone import Microphone
from app.schemas.microphone import MicrophoneResponse

router = APIRouter(prefix="/microphones", tags=["microphones"])

@router.get("/", response_model=List[MicrophoneResponse])
def list_microphones(
    mic_type: Optional[str] = None,
    directionality: Optional[str] = None,
    connection: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Microphone)
    if mic_type:
        query = query.filter(Microphone.mic_type == mic_type)
    if directionality:
        query = query.filter(Microphone.directionality == directionality)
    if connection:
        query = query.filter(Microphone.connection_types.contains(connection))
    if price_max:
        query = query.filter(Microphone.price <= price_max)
    if price_min:
        query = query.filter(Microphone.price >= price_min)
    return query.all()

@router.get("/{mic_id}", response_model=MicrophoneResponse)
def get_microphone(mic_id: int, db: Session = Depends(get_db)):
    mic = db.query(Microphone).filter(Microphone.id == mic_id).first()
    if not mic:
        raise HTTPException(status_code=404, detail="Microphone not found")
    return mic
