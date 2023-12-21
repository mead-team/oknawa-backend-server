from pydantic import BaseModel, Field


class Hotplace(BaseModel):
    address_name: str
    category_group_code: str
    category_group_name: str
    category_name: str
    distance: str
    id: str
    phone: str
    place_name: str
    place_url: str
    road_address_name: str
    x: str
    y: str


class Meta(BaseModel):
    is_end: bool
    pageable_count: int
    total_count: int


class PostLocationPoint(BaseModel):
    station_name: str = Field(title="역이름", description="역이름")
    address_name: str = Field(title="도로명 주소", description="도로명 주소")
    end_x: float = Field(title="x좌표", description="x좌표")
    end_y: float = Field(title="y좌표", description="y좌표")
    share_key: str = Field(title="공유 param key", description="공유 param key")
    itinerary: list


class GetLocationPoint(PostLocationPoint):
    pass


class PostPopularMeetingLocation(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class GetPopularMeetingLocation(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class GetPointPlace(BaseModel):
    documents: list[Hotplace]
    meta: Meta
