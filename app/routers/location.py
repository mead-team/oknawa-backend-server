from fastapi import APIRouter
from app.schemas.base import RouterTags


router = APIRouter(prefix="/location", tags=[RouterTags.location])


@router.post(
    "/temp1",
    summary="temp 중간지점 찾기",
)
def temp1():
    return {}


@router.get(
    "/hotplace",
    # response_model=res_user.Get200InvestmentTierHistory,
    summary="핫플레이스 리스트",
)
def hotplace(
    q: RequestHotplace = Depends()
):
    return {}