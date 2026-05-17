from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Mouse(Base, TimestampMixin):
    __tablename__ = "mice"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    sensor = Column(String)
    switches = Column(String)
    weight_g = Column(Float)
    connection_types = Column(String)
    button_count = Column(Integer)
    max_dpi = Column(Integer)
    color = Column(String)
    form_factor = Column(String)
    has_rgb = Column(Boolean, default=False)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    dns_sku = Column(String, unique=True, nullable=True)
    dns_url = Column(String, nullable=True)
    dns_price = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
