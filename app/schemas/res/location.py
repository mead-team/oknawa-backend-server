from pydantic import BaseModel, Field


class PostLocationPoint(BaseModel):
    station_name: str = Field(title="역이름", description="역이름")
    address_name: str = Field(title="도로명 주소", description="도로명 주소")
    x: str = Field(title="x좌표", description="x좌표")
    y: str = Field(title="y좌표", description="y좌표")