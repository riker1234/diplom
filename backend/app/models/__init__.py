from sqlalchemy import Column, DateTime, Float, Integer
from sqlalchemy.sql import func

class TimestampMixin:
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RatingMixin:
    """Per-source rating + review count (shown in catalog card & product modal)."""
    ozon_rating = Column(Float, nullable=True)
    ozon_reviews = Column(Integer, nullable=True)
    citilink_rating = Column(Float, nullable=True)
    citilink_reviews = Column(Integer, nullable=True)
    wb_rating = Column(Float, nullable=True)
    wb_reviews = Column(Integer, nullable=True)
