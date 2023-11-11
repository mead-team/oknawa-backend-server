from pydantic import BaseModel, Field


class Participant(BaseModel):
    name: str = Field(title="참여자 이름", description="참여자 이름")
    x: str = Field(title="x좌표", description="x좌표")
    y: str = Field(title="y좌표", description="y좌표")


class PostLocationPoint(BaseModel):
    participant: list[Participant] = Field(title="참여자", description="참여자")
