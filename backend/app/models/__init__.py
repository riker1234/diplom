from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

class TimestampMixin:
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
