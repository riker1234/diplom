from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class StoreAvailability(Base):
    __tablename__ = "store_availability"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False)
    product_id = Column(Integer, nullable=False)
    dns_product_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    store_address = Column(String, nullable=False)
    store_name = Column(String, nullable=True)
    in_stock = Column(Boolean, default=True)
