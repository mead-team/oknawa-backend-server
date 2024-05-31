import asyncio
from typing import Literal, List, Union

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, WebSocket, WebSocketDisconnect

from redis import Redis
from sqlalchemy.orm import Session

from app.core.socket import ConnectionManager, get_socket_manager
from app.core.dependency import get_db, get_redis
from app.schemas.base import RouterTags
from app.schemas.req import location as req_location
from app.schemas.res import location as res_location
from app.services import location as service_location

router = APIRouter(prefix="/location", tags=[RouterTags.location])



@router.post(
    "/point",
    status_code=200,
    response_model=res_location.PostLocationPoint,
    summary="사용자들간의 중간지점역 찾기",
)
def post_location_point(
    body: req_location.PostLocationPoint,
    api_type: Literal["t_map", "google_map"] | None = Query(default=None, title="Map API 종류", description="t_map or google_map"),
    priority: int = Query(default=0, ge=0, le=4, title="n번째 가까운 위치", description="n번째 가까운 위치"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    todo: 구글 API로 완전 이전시 request의 api_type 쿼리스트링 삭제 예정
    """
    return service_location.post_location_point(body, api_type, priority, db, redis)


@router.post(
    "/points",
    status_code=200,
    response_model=res_location.PostLocationPoints,
    summary="사용자들간의 중간지점역 찾기",
)
def post_location_points(
    body: req_location.PostLocationPoint,
    api_type: Literal["t_map", "google_map"] | None = Query(default=None, title="Map API 종류", description="t_map or google_map"),
    priority: int = Query(default=1, ge=1, le=4, title="가까운 위치 개수", description="가까운 위치 개수 min 1 ~ max 4"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    todo: 구글 API로 완전 이전시 request의 api_type 쿼리스트링 삭제 예정
    """
    return service_location.post_location_points(body, api_type, priority, db, redis)


@router.get(
    "/point",
    status_code=200,
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
    status_code=200,
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
    summary="주요 지하철역 데이터 DB Upsert",
)
def post_popular_meeting_location(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    background_tasks.add_task(service_location.post_popular_meeting_location, db, redis)
    return {"msg": "DB Update Trigger"}


@router.websocket("/ws-together")
async def websocket_endpoint(
    websocket: WebSocket,
    query: req_location.GetTogetherRoomId = Depends(),
    socket_manager: ConnectionManager = Depends(get_socket_manager),
    redis: Redis = Depends(get_redis)
):
    await service_location.websocket_handler(websocket, query, socket_manager, redis)

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
    response_model=Union[res_location.PutTogetherHost | res_location.PutTogetherClient],
    summary="함께 입력 호스트/클라이언트 출발지 수정",
)
def put_together_location(
    body: req_location.PutTogetherLocationPoint,
    query: req_location.PutTogetherRoomId = Depends(),
    redis: Redis = Depends(get_redis),
):
    return service_location.put_together_location(body, query, redis)
