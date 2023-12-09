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
    itinerary: list


class PostPopularMeetingLocation(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class PopularMeetingLocation(BaseModel):
    subway_name: str = Field(title="지하철역 이름", description="지하철역 이름")
    total_passenger: float = Field(title="전체 이용 인원", description="전체 이용 인원")
    using_date: str = Field(title="이용 날짜", description="이용 날짜")


class GetPopularMeetingLocation(BaseModel):
    msg: list[PopularMeetingLocation] = Field(
        title="주요 지하철역 리스트", description="주요  지하철역 리스트"
    )


class GetPointPlace(BaseModel):
    documents: list[Hotplace]
    meta: Meta
