from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Path
from redis import Redis
from sqlalchemy.orm import Session

from app.core.dependency import get_db, get_redis
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location as service_location

router = APIRouter(prefix="/location", tags=[RouterTags.location])


@router.post(
    "/point",
    response_model=res_location.PostLocationPoint,
    summary="사용자들간의 중간지점역 찾기",
)
def post_location_point(
    body: req_location.PostLocationPoint,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_location_point(body, db, redis)


@router.get(
    "/point",
    response_model=res_location.GetLocationPoint,
    summary="share key를 이용한 사용자들간의 중간지점역 찾기",
)
def get_location_point(
    query: req_location.GetLocationPoint = Depends(),
    redis: Redis = Depends(get_redis),
):
    return service_location.get_location_point(query, redis)


@router.get(
    "/point/place/{category}",
    response_model=res_location.GetPointPlace,
    summary="중간지점역의 핫플레이스(만날장소) 리스트",
)
async def get_point_place(
    category: Literal["food", "cafe", "drink"] = Path(),
    query: req_location.GetPointPlace = Depends(),
):
    response = await service_location.get_point_place(category, query)
    return response


@router.post(
    "/meeting",
    response_model=res_location.PostPopularMeetingLocation,
    summary="주요 지하철역 리스트 DB 최신화",
)
def post_popular_meeting_location(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    background_tasks.add_task(service_location.post_popular_meeting_location, db, redis)
    return {"msg": "DB Update Trigger"}
