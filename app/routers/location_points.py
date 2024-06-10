from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
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
        title="가까운 위치 개수",
        description="가까운 위치 개수 min 1 ~ max 4",
    ),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    todo: 구글 API로 완전 이전시 request의 api_type 쿼리스트링 삭제 예정
    """
    return service_location.post_location_points(body, api_type, priority, db, redis)


@router.get(
    "/points/{point_id}",
    status_code=200,
    response_model=res_location.GetLocationPoints,
    summary="✅ point_id를 이용한 사용자들간의 중간지점역 찾기 (결과지도페이지 4개)",
)
def get_location_points(
    point_id: str = Path(title="공유 param key", description="공유 param key"),
    redis: Redis = Depends(get_redis),
):
    return service_location.get_location_points(point_id, redis)


@router.post(
    "/points/{point_id}/vote",
    status_code=200,
    response_model=res_location.PostLocationPointsVote,
    summary="선호도 투표 하기",
)
def post_location_points_vote(
    point_id: str = Path(title="공유 param key", description="공유 param key"),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_location_points_vote(point_id, redis)


@router.get(
    "/points/{point_id}/vote",
    status_code=200,
    response_model=res_location.GetLocationPointsVote,
    summary="선호도 투표 결과(목록) Server Sent Event",
)
def get_location_points_vote(
    point_id: str = Path(title="공유 param key", description="공유 param key"),
    redis: Redis = Depends(get_redis),
):
    return service_location.get_location_points_vote(point_id, redis)


@router.post(
    "/points/{point_id}/confirm",
    status_code=200,
    response_model=res_location.PostLocationPointsConfirm,
    summary="선호도 투표 확정",
)
def post_location_points_confirm(
    point_id: str = Path(title="공유 param key", description="공유 param key"),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_location_points_conirm(point_id, redis)
