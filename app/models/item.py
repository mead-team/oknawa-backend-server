from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from app.core.database import Base


class Item(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
