from enum import Enum

from pydantic import BaseModel, Field


class RequestHotplace(BaseModel):
    category_group_code: str = Field("CE7", title="카테고리 코드", description="카테고리 코드")
    x: str = Field(3, title="x좌표", description="x좌표")
    y: str = Field(9, title="y좌표", description="y좌표")
    radius: int = Field(500, title="범위 (미터)", description="범위")
