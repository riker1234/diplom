from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MicrophoneResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    mic_type: Optional[str] = None
    directionality: Optional[str] = None
    connection_types: Optional[str] = None
    frequency_range: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class MicrophoneCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    mic_type: Optional[str] = None
    directionality: Optional[str] = None
    connection_types: Optional[str] = None
    frequency_range: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
