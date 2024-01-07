from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class Timestamp:
    created_at = Column(
        DateTime, nullable=False, server_default=func.now(), comment="생성일시"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="수정일시",
    )
    deleted_at = Column(DateTime, nullable=True, comment="삭제일시")
