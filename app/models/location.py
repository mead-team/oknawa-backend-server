from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from app.core.database import Base
from app.models.base import Timestamp


class PopularMeetingLocation(Timestamp, Base):
    __tablename__ = "popular_meeting_location"
    __table_args__ = {"comment": "인기 있는 만남의 장소"}

    id = Column(Integer, primary_key=True, nullable=False, index=True, comment="PK")
    name = Column(String, nullable=False, comment="위치 이름")
    type = Column(String, nullable=False, comment="위치 타입")
    url = Column(String, nullable=False, comment="위치 url")
    address = Column(String, nullable=False, comment="위치 주소")
    location_x = Column(Float, nullable=False, comment="x좌표")
    location_y = Column(Float, nullable=False, comment="y좌표")
