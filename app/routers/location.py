from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Path
from sqlalchemy.orm import Session

from app.core.dependency import get_db
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
    body: req_location.PostLocationPoint, db: Session = Depends(get_db)
):
    return service_location.post_location_point(body, db)


@router.get(
    "/point/place/{category}",
    response_model=res_location.GetPointPlace,
    summary="중간지점역의 핫플레이스(만날장소) 리스트",
)
def get_point_place(
    category: Literal["food", "cafe", "drink"] = Path(),
    query: req_location.GetPointPlace = Depends(),
):
    return service_location.get_point_place(category, query)


@router.post(
    "/meeting",
    response_model=res_location.PostPopularMeetingLocation,
    summary="주요 지하철역 리스트 DB 최신화",
)
def post_popular_meeting_location(background_tasks: BackgroundTasks):
    background_tasks.add_task(service_location.post_popular_meeting_location)
    return {"msg": "DB Update Trigger"}
