from fastapi import APIRouter, Depends, Path, Query
from redis import Redis

from app.core.dependency import get_redis
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location_together as service_location_together

router = APIRouter(prefix="/location", tags=[RouterTags.location_together])


@router.post(
    "/together",
    status_code=201,
    response_model=res_location.PostTogetherHost,
    summary="✅ 함께 입력 호스트 출발지 입력 및 공간 생성",
)
def post_together(
    body: req_location.Participant,
    redis: Redis = Depends(get_redis),
):
    return service_location_together.post_together(body, redis)


@router.get(
    "/together/{room_id}/polling",
    status_code=200,
    response_model=res_location.GetTogetherLocation,
    summary="✅ 함께 입력 현황 조회 polling",
)
def get_together_location_polling(
    room_id: str = Path(title="출발지 입력방 ID", description="출발지 입력방 ID"),
    redis: Redis = Depends(get_redis),
):
    response = service_location_together.get_together_location_polling(room_id, redis)
    return response


@router.get(
    "/together/{room_id}/long-polling",
    status_code=200,
    response_model=res_location.GetTogetherLocation,
    summary="✅ 함께 입력 현황 조회 long_polling",
)
def get_together_location_long_polling(
    room_id: str = Path(title="출발지 입력방 ID", description="출발지 입력방 ID"),
    redis: Redis = Depends(get_redis),
):
    response = service_location_together.get_together_location_long_polling(
        room_id, redis
    )
    return response


@router.post(
    "/together/{room_id}",
    status_code=201,
    response_model=res_location.PostTogetherClient,
    summary="✅ 함께 입력 클라이언트 출발지 입력",
)
def post_together_location(
    body: req_location.Participant,
    room_id: str = Path(title="출발지 입력방 ID", description="출발지 입력방 ID"),
    redis: Redis = Depends(get_redis),
):
    return service_location_together.post_together_location(body, room_id, redis)


@router.put(
    "/together/{room_id}",
    status_code=200,
    response_model=res_location.PutTogetherHost,
    summary="✅ 함께 입력 호스트/클라이언트 출발지 수정",
)
def put_together_location(
    body: req_location.PutTogetherLocationPoint,
    room_id: str = Path(title="출발지 입력방 ID", description="출발지 입력방 ID"),
    room_host_id: str = Query(
        title="출발지 입력방 방장ID", description="출발지 입력방 방장ID"
    ),
    redis: Redis = Depends(get_redis),
):
    return service_location_together.put_together_location(
        body, room_id, room_host_id, redis
    )
