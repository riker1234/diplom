from sqlalchemy import Column, Integer, String, Float
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
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
