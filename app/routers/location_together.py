from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.core.dependency import get_db, get_redis
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location as service_location

router = APIRouter(prefix="/location", tags=[RouterTags.location_together])


@router.get(
    "/together",
    status_code=200,
    response_model=res_location.GetTogetherLocation,
    summary="함께 입력 현황 조회",
)
def get_together_location(
    query: req_location.GetTogetherRoomId = Depends(),
    redis: Redis = Depends(get_redis),
):
    response = service_location.get_together_location(query, redis)
    return response


@router.post(
    "/together",
    status_code=201,
    response_model=res_location.PostTogetherHost,
    summary="함께 입력 호스트 출발지 입력 및 공간 생성",
)
def post_together(
    body: req_location.Participant,
    redis: Redis = Depends(get_redis),
):
    return service_location.post_together(body, redis)


@router.post(
    "/together/point",
    status_code=201,
    response_model=res_location.PostTogetherClient,
    summary="함께 입력 클라이언트 출발지 입력",
)
def post_together_location(
    body: req_location.Participant,
    query: req_location.PostTogetherRoomId = Depends(),
    redis: Redis = Depends(get_redis),
):
    return service_location.post_together_location(body, query, redis)


@router.put(
    "/together/point",
    status_code=200,
    response_model=res_location.PutTogetherHost,
    summary="함께 입력 호스트/클라이언트 출발지 수정",
)
def put_together_location(
    body: req_location.PutTogetherLocationPoint,
    query: req_location.PutTogetherRoomId = Depends(),
    redis: Redis = Depends(get_redis),
):
    return service_location.put_together_location(body, query, redis)
