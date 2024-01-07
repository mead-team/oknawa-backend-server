from typing import Literal

from pydantic import BaseModel, Field


class Participant(BaseModel):
    name: str = Field(title="참여자 이름", description="참여자 이름")
    region_name: str = Field(title="참여자 주소", description="참여자 주소")
    start_x: float = Field(title="참여자 시작 x좌표", description="x좌표")
    start_y: float = Field(title="참여자 시작 y좌표", description="y좌표")


class PostLocationPoint(BaseModel):
    participant: list[Participant] = Field(title="참여자", description="참여자")


class GetPointPlace(BaseModel):
    x: float = Field(title="인기있는역 x좌표", description="x좌표")
    y: float = Field(title="인기있는역 y좌표", description="y좌표")
    radius: int = Field(500, title="범위 (미터)", description="범위")
    page: int = Field(1, title="범위 (미터)", description="범위")
    size: int = Field(5, title="범위 (미터)", description="범위")
    sort: str = Field("accuracy", title="범위 (미터)", description="범위")


class GetLocationPoint(BaseModel):
    share_key: str = Field(title="공유 param key", description="공유 param key")
