from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from redis import Redis
from sqlalchemy.orm import Session

from app.core.dependency import get_db, get_redis
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location as service_location

router = APIRouter(prefix="/location", tags=[RouterTags.location_points])


@router.post(
    "/points",
    status_code=200,
    response_model=res_location.PostLocationPoints,
    summary="✅ 사용자들간의 중간지점역 찾기 (추천받기)",
)
def post_location_points(
    body: req_location.PostLocationPoint,
    api_type: Literal["t_map", "google_map"] | None = Query(
        default=None, title="Map API 종류", description="t_map or google_map"
    ),
    priority: int = Query(
        default=4,
        ge=1,
        le=4,
        title="중간지점역 개수",
        description="중간지점역 개수 min 1 ~ max 4",
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    todo: 구글 API로 완전 이전시 request의 api_type 쿼리스트링 삭제 예정
    """
    return service_location.post_location_points(body, api_type, priority, db, redis)


@router.get(
    "/points/{map_id}/polling",
    status_code=200,
    response_model=res_location.GetLocationPoints,
    summary="✅ map_id를 이용한 사용자들간의 중간지점역 찾기 (결과지도페이지 4개) polling",
)
def get_location_points(
    map_id: str = Path(
        title="(결과지도페이지 4개) ID", description="(결과지도페이지 4개) ID"
    ),
    redis: Redis = Depends(get_redis),
):
    return service_location.get_location_points(map_id, redis)


@router.get(
    "/points/{map_id}/long-polling",
    status_code=200,
    response_model=res_location.GetLocationPoints,
    summary="✅ map_id를 이용한 사용자들간의 중간지점역 찾기 (결과지도페이지 4개) long polling",
)
def get_location_points_long_polling(
    map_id: str = Path(
        title="(결과지도페이지 4개) ID", description="(결과지도페이지 4개) ID"
    ),
    redis: Redis = Depends(get_redis),
):
    return service_location.get_location_points_long_polling(map_id, redis)


@router.get(
    "/points/{map_id}/sse",
    status_code=200,
    response_model=res_location.GetLocationPoints,
    summary="🔄 map_id를 이용한 사용자들간의 중간지점역 찾기 (결과지도페이지 4개) Server-Sent-Event // 아직작업중...ㅠㅠ",
)
async def get_location_points_sse(
    request: Request,
    map_id: str = Path(
        title="(결과지도페이지 4개) ID", description="(결과지도페이지 4개) ID"
    ),
    redis: Redis = Depends(get_redis),
):
    return await service_location.get_location_points_long_sse(request, map_id, redis)


@router.post(
    "/points/{map_id}/vote",
    status_code=200,
    response_model=res_location.PostLocationPointsVote,
    summary="✅ 선호도 투표 하기",
)
def post_location_points_vote(
    map_id: str = Path(
        title="(결과지도페이지 4개) ID", description="(결과지도페이지 4개) ID"
    ),
    share_key: str = Query(title="중간지점역 키", description="중간지점역 키"),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_location_points_vote(map_id, share_key, redis)


@router.post(
    "/points/{map_id}/confirm",
    status_code=200,
    response_model=res_location.PostLocationPointsConfirm,
    summary="✅ 선호도 투표 확정",
)
def post_location_points_confirm(
    map_id: str = Path(
        title="(결과지도페이지 4개) ID", description="(결과지도페이지 4개) ID"
    ),
    map_host_id: str = Query(title="추천받기 방장 ID", description="추천받기 방장 ID"),
    share_key: str = Query(title="중간지점역 키", description="중간지점역 키"),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_location_points_conirm(
        map_id, map_host_id, share_key, redis
    )
