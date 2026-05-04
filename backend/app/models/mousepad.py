from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Mousepad(Base, TimestampMixin):
    __tablename__ = "mousepads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    size = Column(String)
    surface_material = Column(String)
    hardness = Column(String)
    has_rgb = Column(Boolean, default=False)
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
