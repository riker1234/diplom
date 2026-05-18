from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KeyboardResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    switches: Optional[str] = None
    board_material: Optional[str] = None
    form_factor: Optional[str] = None
    keycap_material: Optional[str] = None
    keycap_manufacturing: Optional[str] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    wb_price: Optional[float] = None
    image_url: Optional[str] = None
    ozon_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    source: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class KeyboardCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    switches: Optional[str] = None
    board_material: Optional[str] = None
    form_factor: Optional[str] = None
    keycap_material: Optional[str] = None
    keycap_manufacturing: Optional[str] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
