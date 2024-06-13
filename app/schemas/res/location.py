from typing import List

from pydantic import AnyUrl, BaseModel, Field


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
    main_photo_url: AnyUrl | None
    open_hour: dict | None


class Meta(BaseModel):
    is_end: bool
    pageable_count: int
    total_count: int


class Participant(BaseModel):
    name: str = Field(title="참여자 이름", description="참여자 이름")
    region_name: str = Field(title="참여자 주소", description="참여자 주소")
    start_x: float = Field(title="참여자 시작 x좌표", description="x좌표")
    start_y: float = Field(title="참여자 시작 y좌표", description="y좌표")


class PostRequestInfo(BaseModel):
    participant: list[Participant] = Field(title="참여자", description="참여자")


class PostLocationPoint(BaseModel):
    station_name: str = Field(title="역이름", description="역이름")
    address_name: str = Field(title="도로명 주소", description="도로명 주소")
    end_x: float = Field(title="x좌표", description="x좌표")
    end_y: float = Field(title="y좌표", description="y좌표")
    share_key: str = Field(title="공유 param key", description="공유 param key")
    vote: int = Field(default=0, title="투표수", description="투표수")
    itinerary: list = Field(
        title="외부MAP API 데이터", description="외부MAP API 데이터"
    )
    request_info: PostRequestInfo = Field(title="요청 정보", description="요청 정보")


class PostLocationPoints(BaseModel):
    map_id: str = Field(title="추천받기 방 ID", description="추천받기 방 ID")
    map_host_id: str = Field(title="추천받기 방장 ID", description="추천받기 방장 ID")


class GetLocationPoints(PostLocationPoints):
    map_host_id: str = Field(exclude=True)
    station_info: list[PostLocationPoint] = Field(
        title="중간지점역 정보 리스트", description="중간지점역 정보 리스트"
    )
    request_info: PostRequestInfo = Field(title="요청 정보", description="요청 정보")
    confirmed: str | None = Field(
        default=None,
        title="선호도투표 확정키",
        description="확정된 중간지점역 share_key",
    )


class PostLocationPointsVote(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class PostLocationPointsConfirm(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class GetLocationPoint(PostLocationPoint):
    pass


class PostPopularMeetingLocation(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class GetPopularMeetingLocation(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class GetPointPlace(BaseModel):
    documents: list[Hotplace]
    meta: Meta


class TogetherParticipant(BaseModel):
    name: str = Field(title="참여자 이름", description="참여자 이름")
    region_name: str = Field(title="참여자 주소", description="참여자 주소")
    start_x: float = Field(title="참여자 시작 x좌표", description="x좌표")
    start_y: float = Field(title="참여자 시작 y좌표", description="y좌표")


class GetTogetherLocation(BaseModel):
    room_id: str = Field(title="함께 입력 공간 uuid", description="함께 입력 공간 uuid")
    participant: List[TogetherParticipant] = Field(
        [], title="함께 입력 현황", description="함께 입력 현황"
    )


class PostTogetherHost(BaseModel):
    room_id: str = Field(title="함께 입력 공간 uuid", description="함께 입력 공간 uuid")
    room_host_id: str = Field(title="호스트 uuid", description="호스트 uuid")


class PostTogetherClient(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")


class PutTogetherHost(BaseModel):
    msg: str = Field(title="응답 메시지", description="응답 메시지")
