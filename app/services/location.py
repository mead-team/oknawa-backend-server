import asyncio
import json
import time
import uuid
from datetime import datetime

import aiohttp
import requests
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.setting import settings
from app.core.util import aiohttp_util, distance_calculator, generate_key, open_api
from app.crud import location
from app.models.location import PopularMeetingLocation


def post_location_point(body, api_type, priority, db, redis):
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
    body_data = body.model_dump()
    popular_location_in_db = location.get_popular_meeting_location_all(db)
    center_coordinates = distance_calculator.get_center_coordinates(body_data)
    center_location_data = distance_calculator.get_center_location(
        center_coordinates, popular_location_in_db, priority
    )
    if api_type == "google_map":
        participant_itinerary = open_api.call_googlemap_api_participant_itinerary(
            body, center_location_data
        )
    elif api_type == "t_map" or api_type is None:
        participant_itinerary = open_api.call_tmap_api_participant_itinerary(
            body, center_location_data
        )
    else:
        raise HTTPException(status_code=404, detail="Not Found")

    response = {
        "station_name": center_location_data.name,
        "address_name": center_location_data.address,
        "end_x": center_location_data.location_x,
        "end_y": center_location_data.location_y,
        "share_key": str(uuid.uuid4()),
        "itinerary": participant_itinerary,
        "request_info": body_data,
    }
    share_key = response.get("share_key")
    redis_point_id_key = f"point-{share_key}"

    redis.set(redis_point_id_key, json.dumps(response), ex=TTL)

    return response


def post_location_points(body, api_type, priority, db, redis):
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
    map_id = str(uuid.uuid4())
    map_host_id = str(uuid.uuid4())
    redis_map_id_key = f"map-{map_id}"

    body_data = body.model_dump()
    popular_location_in_db = location.get_popular_meeting_location_all(db)
    center_coordinates = distance_calculator.get_center_coordinates(body_data)
    center_location_data_list = distance_calculator.get_center_locations(
        center_coordinates, popular_location_in_db, priority
    )

    if api_type == "google_map":
        station_info_list = open_api.call_googlemap_api_participant_itineraries(
            body, center_location_data_list
        )
    elif api_type == "t_map" or api_type is None:
        station_info_list = open_api.call_tmap_api_participant_itineraries(
            body, center_location_data_list
        )
    else:
        raise HTTPException(status_code=404, detail="Not Found")

    for station_info in station_info_list:
        station_info["share_key"] = str(uuid.uuid4())
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

    points_exists_in_redis = redis.get(redis_map_id_key)

    if points_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")

    response = json.loads(points_exists_in_redis.decode("utf-8"))
    return response


def get_location_points_long_polling(map_id, redis):
    timeout = 30
    redis_map_id_key = f"map-{map_id}"

    start_time = time.time()

    previous_points_exists_in_redis = redis.get(redis_map_id_key)
    if previous_points_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")

    while True:
        current_points_exists_in_redis = redis.get(redis_map_id_key)
        if current_points_exists_in_redis is None:
            raise HTTPException(status_code=404, detail="Not Found")

        if previous_points_exists_in_redis != current_points_exists_in_redis:
            response = json.loads(current_points_exists_in_redis.decode("utf-8"))
            return response

        if time.time() - start_time > timeout:
            response = json.loads(current_points_exists_in_redis.decode("utf-8"))
            return response
        time.sleep(1)


async def get_location_points_long_sse(request: Request, map_id, redis):
    async def event_generator(request):
        redis_map_id_key = f"map-{map_id}"

        previous_points_exists_in_redis = redis.get(redis_map_id_key)
        if previous_points_exists_in_redis is None:
            raise HTTPException(status_code=404, detail="Not Found")

        while True:
            if await request.is_disconnected():
                print("Client disconnected")
                break

            response = None
            current_points_exists_in_redis = redis.get(redis_map_id_key)
            if current_points_exists_in_redis is None:
                raise HTTPException(status_code=404, detail="Not Found")

            if previous_points_exists_in_redis != current_points_exists_in_redis:
                response = json.loads(current_points_exists_in_redis.decode("utf-8"))
                previous_points_exists_in_redis = current_points_exists_in_redis

            if response:
                yield f"{json.dumps(response)}\n\n"

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator(request))


def post_location_points_vote(map_id, share_key, redis):
    """선호도 투표 하기
    redis에서 선호도투표 데이터 가져와서 vote 1씩 올리고 다시저장

    Args:
        map_id (str): _description_
        share_key (str): _description_
        redis (_type_): _description_
    """
    redis_map_id_key = f"map-{map_id}"

    points_exists_in_redis = redis.get(redis_map_id_key)

    if points_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")

    points = dict(json.loads(points_exists_in_redis.decode("utf-8")))

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
    """선호도 투표 확정
    confirmed에 share key 넣기,
    Redis에 hset 해시는 point share key를 필드로 확정된 결과 1개 저장
    Args:
        map_id (_type_): _description_
        map_host_id (_type_): _description_
        share_key (_type_): _description_
        redis (_type_): _description_
    """
    TTL = 60 * 60 * 24 * 14
    redis_map_id_key = f"map-{map_id}"

    points_exists_in_redis = redis.get(redis_map_id_key)

    if points_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")

    points = dict(json.loads(points_exists_in_redis.decode("utf-8")))

    if points.get("map_host_id") != map_host_id:
        raise HTTPException(status_code=404, detail="Invalid Map Host ID")

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
    # redis_map_id_key 데이터를 지워야할지?

    return {"msg": "투표 확정 완료"}


def get_location_point(query, redis):
    share_key = query.share_key
    redis_point_id_key = f"point-{share_key}"
    share_key_exists_in_redis = redis.get(redis_point_id_key)

    if share_key_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")
    else:
        response = json.loads(share_key_exists_in_redis.decode("utf-8"))
        return response


async def get_point_place(path, query):
    KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

    query = query.model_dump()
    if path == "food":
        query.update(category_group_code="FD6", query="음식점")
    elif path == "drink":
        query.update(category_group_code="FD6", query="술집")
    elif path == "cafe":
        query.update(category_group_code="CE7", query="카페")

    async with aiohttp.ClientSession() as session:
        response = await aiohttp_util.fetch(url, session, headers, query)

        tasks = []
        for document in response.get("documents"):
            place_url = document.get("place_url")
            place_url_id = place_url.split("/")[-1]
            replace_suburl = f"main/v/{place_url_id}"
            place_api_url = place_url.replace(place_url_id, replace_suburl)
            tasks.append(aiohttp_util.get_place_info(place_api_url))

        api_responses = await asyncio.gather(*tasks)

        for document, api_response in zip(response.get("documents"), api_responses):
            api_basic_info = api_response.get("basicInfo")
            document.update(main_photo_url=api_basic_info.get("mainphotourl"))
            document.update(open_hour=api_basic_info.get("openHour"))

    return response


def post_popular_meeting_location(db, redis):
    KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
    current_time = datetime.utcnow()
    print(f"popular meeting location update trigger start : {current_time}")

    open_api_data = open_api.call_open_data_api_popular_subway()
    popular_subway_redis_data = redis.get("popular_subway")

    if popular_subway_redis_data is None:
        redis.set("popular_subway", json.dumps(open_api_data))
    else:
        redis_data = json.loads(popular_subway_redis_data.decode("utf-8"))
        added_data = [
            data
            for data in open_api_data
            if data["subway_name"] not in {item["subway_name"] for item in redis_data}
        ]
        exists_data = [
            data
            for data in redis_data
            if data["subway_name"] in {item["subway_name"] for item in open_api_data}
        ]
        redis.set("popular_subway", json.dumps(exists_data + added_data))

    popular_subway_in_redis = json.loads(redis.get("popular_subway").decode("utf-8"))
    subway_name_list = [data["subway_name"] for data in popular_subway_in_redis]
    popular_meeting_location_obj = []
    for subway_name in subway_name_list:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {"query": subway_name}
        api_response = requests.get(url, headers=headers, params=params)

        for kakao_data in api_response.json()["documents"]:
            if kakao_data["category_group_name"] == "지하철역":
                popular_meeting_location_exists_in_db = (
                    location.get_popular_meeting_location_first(
                        db, kakao_data["place_name"], kakao_data["x"], kakao_data["y"]
                    )
                )
                if not popular_meeting_location_exists_in_db:
                    location_obj = PopularMeetingLocation(
                        name=kakao_data["place_name"],
                        type="station",
                        url=kakao_data["place_url"],
                        address=kakao_data["road_address_name"],
                        location_x=kakao_data["x"],
                        location_y=kakao_data["y"],
                    )
                    popular_meeting_location_obj.append(location_obj)
                else:
                    popular_meeting_location_exists_in_db.updated_at = current_time
                break

    location.create_popular_meeting_location(db, popular_meeting_location_obj)
    location.delete_popular_meeting_location(db, current_time)
    response = {
        "msg": "인기 있는 장소 최신화 완료",
    }
    print(f"popular meeting location update trigger done : {current_time}")
    return response


def get_together_location(query, redis):
    room_id = query.room_id
    generate_key.validate_uuid(room_id)

    room_data = redis.get(room_id)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    participant_data = json.loads(room_data).get("participant")
    response = {"room_id": room_id, "participant": participant_data}
    return response


def post_together(body, redis):
    TTL = 60 * 60 * 24 * 14
    room_id = generate_key.create_uuid()
    host_id = room_id.replace("-", "")[:8][::-1]
    host_start_point = body.dict()

    room_data = {"host_id": host_id, "participant": [host_start_point]}

    redis.set(room_id, json.dumps(room_data), ex=TTL)
    return {"room_id": room_id, "host_id": host_id}


def post_together_location(body, query, redis):
    TTL = 60 * 60 * 24 * 14
    room_id = query.room_id
    generate_key.validate_uuid(room_id)

    room_data = redis.get(room_id)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    client_start_point = body.dict()
    room_data = json.loads(room_data)
    room_data["participant"].append(client_start_point)

    redis.set(room_id, json.dumps(room_data), ex=TTL)
    return {"room_id": room_id}


def put_together_location(body, query, redis):
    TTL = 60 * 60 * 24 * 14
    room_id = query.room_id
    host_id = query.host_id
    generate_key.validate_uuid(room_id)

    room_data = redis.get(room_id)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    room_data = json.loads(room_data)
    host_id_data = room_data["host_id"]

    if host_id != host_id_data:
        raise HTTPException(status_code=404, detail="Not Permission")

    body_dict = body.dict().get("participant")
    room_data["participant"] = body_dict
    redis.set(room_id, json.dumps(room_data), ex=TTL)
    return {"room_id": room_id, "host_id": host_id}
