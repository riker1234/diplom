from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Keyboard(Base, TimestampMixin):
    __tablename__ = "keyboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    switches = Column(String)
    board_material = Column(String)
    form_factor = Column(String)
    keycap_material = Column(String)
    keycap_manufacturing = Column(String)
    connection_types = Column(String)
    has_rgb = Column(Boolean, default=False)
    layout = Column(String)
    key_count = Column(Integer)
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
    citilink_sku = Column(String, unique=True, nullable=True)
    citilink_url = Column(String, nullable=True)
    citilink_price = Column(Float, nullable=True)
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
        if self.citilink_sku:
            parts.append("citilink")
        return "+".join(parts) if parts else "unknown"
