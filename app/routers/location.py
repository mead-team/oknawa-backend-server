from fastapi import APIRouter, Depends

from app.schemas import location as schema_location
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location as service_location

router = APIRouter(prefix="/location", tags=[RouterTags.location])


@router.post(
    "/point",
    response_model=res_location.PostLocationPoint,
    summary="중간 지점 찾기",
)
def post_location_point(body: req_location.PostLocationPoint):
    return service_location.get_location_point(body)


@router.get(
    "/point/place",
    response_model=schema_location.ResponseHotplace,
    summary="핫플레이스 리스트",
)
def get_location_point_place(q: schema_location.RequestHotplace = Depends()):
    return service_location.get_location_point_place(q)
