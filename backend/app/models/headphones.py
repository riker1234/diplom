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
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
