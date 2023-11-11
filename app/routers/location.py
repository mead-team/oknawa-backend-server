from fastapi import APIRouter, Depends
from app.schemas.base import RouterTags

from app.schemas import location as schema_location
from app.services import location as service_location


router = APIRouter(prefix="/location", tags=[RouterTags.location])


@router.post(
    "/temp1",
    summary="temp 중간지점 찾기",
)
def temp1():
    return {}


@router.get(
    "/hotplace",
    response_model=schema_location.ResponseHotplace,
    summary="핫플레이스 리스트",
)
def hotplace(
    q: schema_location.RequestHotplace = Depends()
):
    return service_location.hotplace(q)