from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Microphone(Base, TimestampMixin):
    __tablename__ = "microphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    mic_type = Column(String)
    directionality = Column(String)
    connection_types = Column(String)
    frequency_range = Column(String)
    sample_rate = Column(String)
    bit_depth = Column(String)
    color = Column(String)
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

