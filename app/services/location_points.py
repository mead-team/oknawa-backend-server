import asyncio
import json
import time

from fastapi import HTTPException, Request

# from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.util import distance_calculator, generate_key, open_api
from app.crud import location


async def post_location_points(body, api_type, priority, db, redis):
    """
        사용자들의 좌표를 받아 중간지점좌표와 가장가까운 역의 좌표를 구한 뒤
        tmap의 API를 이용하여 소요시간, 가는경로를 구하여 리턴 (도보 - 대중교통 - 도보)

        일단 어떤 데이터만 쓸지 모르기 때문에 API자체를 리턴, 추후에 데이터 정제하여 고도화

        우선순위는 지하철 지하철 데이터가 없을경우엔 최단시간으로 제공

    Args:
        body (obj): /point의 request로 받은 유저별 좌표
        priority(int): n번째로 가까운 지역
        db: get_db
        redis: get_redis

    Returns:
        dict: response 데이터
    """
    TTL = 60 * 60 * 24 * 14
    map_id = generate_key.create_uuid()
    map_host_id = map_id.replace("-", "")[:8][::-1]
    redis_map_id_key = f"map-{map_id}"

    body_data = body.model_dump()
    popular_location_in_db = location.get_popular_meeting_location_all(db)
    center_coordinates = distance_calculator.get_center_coordinates(body_data)
    center_location_data_list = distance_calculator.get_center_locations(
        center_coordinates, popular_location_in_db, priority
    )

    if api_type == "google_map":
        station_info_list = await open_api.call_googlemap_api_participant_itineraries(
            body, center_location_data_list
        )
    elif api_type == "t_map" or api_type is None:
        station_info_list = await open_api.call_tmap_api_participant_itineraries(
            body, center_location_data_list
        )
    else:
        raise HTTPException(status_code=404, detail="Not Found")

    for station_info in station_info_list:
        share_key = generate_key.create_uuid()
        station_info["share_key"] = share_key
        station_info["vote"] = 0
        station_info["request_info"] = body_data

    response = {
        "map_id": map_id,
        "map_host_id": map_host_id,
        "station_info": station_info_list,
        "request_info": body_data,
        "confirmed": None,
    }

    redis.set(redis_map_id_key, json.dumps(response), ex=TTL)

    return response


def get_location_points(map_id, redis):
    redis_map_id_key = f"map-{map_id}"
    generate_key.validate_uuid(map_id)

    points_data = redis.get(redis_map_id_key)

    if points_data is None:
        raise HTTPException(status_code=404, detail="Not Found")

    response = json.loads(points_data.decode("utf-8"))
    return response


def get_location_points_long_polling(map_id, redis):
    timeout = 30
    redis_map_id_key = f"map-{map_id}"
    generate_key.validate_uuid(map_id)

    start_time = time.time()

    previous_points_data = redis.get(redis_map_id_key)
    if previous_points_data is None:
        raise HTTPException(status_code=404, detail="Not Found")

    while True:
        current_points_data = redis.get(redis_map_id_key)
        if current_points_data is None:
            raise HTTPException(status_code=404, detail="Not Found")

        if previous_points_data != current_points_data:
            response = json.loads(current_points_data.decode("utf-8"))
            return response

        if time.time() - start_time > timeout:
            response = json.loads(current_points_data.decode("utf-8"))
            return response
        time.sleep(1)


async def get_location_points_long_sse(request: Request, map_id, redis):
    async def event_generator(request):
        redis_map_id_key = f"map-{map_id}"
        generate_key.validate_uuid(map_id)

        previous_points_data = redis.get(redis_map_id_key)
        if previous_points_data is None:
            raise HTTPException(status_code=404, detail="Not Found")

        while True:
            if await request.is_disconnected():
                print("Client disconnected")
                break

            response = None
            current_points_data = redis.get(redis_map_id_key)
            if current_points_data is None:
                raise HTTPException(status_code=404, detail="Not Found")

            if previous_points_data != current_points_data:
                response = json.loads(current_points_data.decode("utf-8"))
                previous_points_data = current_points_data

            if response:
                yield f"{json.dumps(response)}\n\n"

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator(request))


def post_location_points_vote(map_id, share_key, redis):
    redis_map_id_key = f"map-{map_id}"
    generate_key.validate_uuid(map_id)

    points_data = redis.get(redis_map_id_key)

    if points_data is None:
        raise HTTPException(status_code=404, detail="Not Found")

    points = dict(json.loads(points_data.decode("utf-8")))

    for station_info in points.get("station_info"):
        station_info_share_key = station_info.get("share_key")
        if station_info_share_key == share_key:
            vote = station_info.get("vote")
            station_info.update({"vote": vote + 1})

    ttl = redis.ttl(redis_map_id_key)
    if ttl < 0:
        raise HTTPException(status_code=404, detail="Expire TTL")

    redis.set(redis_map_id_key, json.dumps(points), ex=ttl)

    return {"msg": "투표 완료"}


def post_location_points_conirm(map_id, map_host_id, share_key, redis):
    TTL = 60 * 60 * 24 * 14
    redis_map_id_key = f"map-{map_id}"
    generate_key.validate_uuid(map_id)

    points_data = redis.get(redis_map_id_key)

    if points_data is None:
        raise HTTPException(status_code=404, detail="Not Found")

    points = dict(json.loads(points_data.decode("utf-8")))

    if points.get("map_host_id") != map_host_id:
        raise HTTPException(status_code=404, detail="Not Permission")

    for station_info in points.get("station_info"):
        station_info_share_key = station_info.get("share_key")
        if station_info_share_key == share_key:
            points.update({"confirmed": station_info_share_key})
            redis_point_id_key = f"point-{station_info_share_key}"
            redis.set(redis_point_id_key, json.dumps(station_info), ex=TTL)
            break

    ttl = redis.ttl(redis_map_id_key)
    if ttl < 0:
        raise HTTPException(status_code=404, detail="Expire TTL")

    redis.set(redis_map_id_key, json.dumps(points), ex=ttl)
    # 모든프로세스가 완료되서 룸이 필요없어지면 redis_map_id_key 데이터를 지워야할지? 다시 들어올지..?

    return {"msg": "투표 확정 완료"}
