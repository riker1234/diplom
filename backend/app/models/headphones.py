from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Headphones(Base, TimestampMixin):
    __tablename__ = "headphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    construction_type = Column(String)
    connection_types = Column(String)
    has_microphone = Column(Boolean, default=False)
    noise_cancellation = Column(String)
    frequency_response = Column(String)
    impedance_ohm = Column(Integer)
    color = Column(String)
    has_rgb = Column(Boolean, default=False)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    dns_sku = Column(String, unique=True, nullable=True)
    dns_url = Column(String, nullable=True)
    dns_price = Column(Float, nullable=True)
    wb_sku = Column(String, unique=True, nullable=True)
    wb_url = Column(String, nullable=True)
    wb_price = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)

    @property
    def source(self) -> str:
        parts = []
        if self.ozon_sku:
            parts.append("ozon")
        if self.wb_sku:
            parts.append("wb")
        if self.dns_sku:
            parts.append("dns")
        return "+".join(parts) if parts else "unknown"

