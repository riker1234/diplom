from sqlalchemy import Column, Integer, String, Float
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
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
