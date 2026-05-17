from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Monitor(Base, TimestampMixin):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    diagonal_inch = Column(Float)
    resolution = Column(String)
    refresh_rate_hz = Column(Integer)
    matrix_type = Column(String)
    response_time_ms = Column(Float)
    brightness_nits = Column(Integer)
    hdr = Column(Boolean, default=False)
    color = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
