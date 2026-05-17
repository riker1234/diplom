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
    image_url = Column(String, nullable=True)
