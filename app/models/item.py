from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.core.database import Base
from app.models.base import Timestamp


class Item(Timestamp, Base):
    __tablename__ = "item"
    __table_args__ = {"comment": "아이템"}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
