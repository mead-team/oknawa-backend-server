from typing import Literal

from pydantic import BaseModel, Field


class Participant(BaseModel):
    name: str = Field(title="참여자 이름", description="참여자 이름")
    x: float = Field(title="x좌표", description="x좌표")
    y: float = Field(title="y좌표", description="y좌표")


class PostLocationPoint(BaseModel):
    participant: list[Participant] = Field(title="참여자", description="참여자")


class GetPointPlace(BaseModel):
    category_name: Literal["food", "cafe", "drink"] = Field(
        title="카테고리", description="카테고리"
    )
    x: float = Field(title="x좌표", description="x좌표")
    y: float = Field(title="y좌표", description="y좌표")
    radius: int = Field(500, title="범위 (미터)", description="범위")
    page: int = Field(1, title="범위 (미터)", description="범위")
    size: int = Field(15, title="범위 (미터)", description="범위")
    sort: str = Field("accuracy", title="범위 (미터)", description="범위")
