import re
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.ext.declarative import declarative_base


@as_declarative()
class Base:
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
