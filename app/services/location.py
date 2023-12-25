import json
import uuid
from datetime import datetime
from urllib.parse import quote

import requests
from fastapi import HTTPException

from app.core.dependency import get_db
from app.core.redis import redis_config
from app.core.setting import settings
from app.core.util import distance_calculator, open_api, route_util
from app.crud import location
from app.models.location import PopularMeetingLocation


def post_location_point(body, db):
    """
        사용자들의 좌표를 받아 중간지점좌표와 가장가까운 역의 좌표를 구한 뒤
        tmap의 API를 이용하여 소요시간, 가는경로를 구하여 리턴 (도보 - 대중교통 - 도보)

        일단 어떤 데이터만 쓸지 모르기 때문에 API자체를 리턴, 추후에 데이터 정제하여 고도화

        우선순위는 지하철 지하철 데이터가 없을경우엔 최단시간으로 제공

    Args:
        body (obj): /point의 request로 받은 유저별 좌표

    Returns:
        dict: response 데이터
    """
    centroid_point = distance_calculator.calculate_centroid(body.model_dump())
    place_data_in_db = location.get_popular_meeting_location_all(db)
    location_data = distance_calculator.calculate_distance(
        centroid_point, place_data_in_db
    )

    station_name = location_data.name
    address_name = location_data.address
    end_x = location_data.location_x
    end_y = location_data.location_y

    # Tmap
    transit_url = "https://apis.openapi.sk.com/transit/routes"
    headers = {"appKey": f"{settings.TMAP_REST_API_KEY}"}

    itinerary_list = []
    for participant in body.participant:
        source_and_target = dict(
            startX=participant.start_x,
            startY=participant.start_y,
            endX=end_x,
            endY=end_y,
        )
        transit_response = requests.post(
            transit_url,
            headers=headers,
            json=source_and_target,
        )

        if transit_response.status_code == 200:
            transit_response_json = transit_response.json()
            if transit_response_json.get("metaData"):
                itinerary = route_util.extract_itinerary_list(transit_response_json)
                total_polyline = route_util.extract_polyline(itinerary)
                itinerary.update(total_polyline=total_polyline)
                itinerary_list.append(dict(name=participant.name, itinerary=itinerary))
            else:
                if transit_response_json.get("result", {}).get("status") == 11:
                    # 거리가 너무 가까운경우
                    pedestrian_url = (
                        "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
                    )
                    start_name = quote(participant.name, encoding="utf-8")
                    end_name = quote(location_data.name, encoding="utf-8")
                    source_and_target.update(startName=start_name, endName=end_name)
                    pedestrian_response = requests.post(
                        pedestrian_url,
                        headers=headers,
                        json=source_and_target,
                    )
                    pedestrian_response_json = pedestrian_response.json()
                    if pedestrian_response.status_code == 200:
                        itinerary = {}
                        total_polyline = []
                        features = pedestrian_response_json.get("features")
                        for feature in features:
                            properties = feature.get("properties")
                            if properties.get("pointType") == "SP":
                                itinerary.update(totalTime=properties.get("totalTime"))
                                lng, lat = feature.get("geometry").get("coordinates")
                                total_polyline.append({"lng": lng, "lat": lat})
                            if not properties.get("pointType"):
                                coordinates = feature.get("geometry").get("coordinates")
                                for coordinate in coordinates[1:]:
                                    lng, lat = coordinate
                                    total_polyline.append({"lng": lng, "lat": lat})
                        itinerary.update(total_polyline=total_polyline)
                        itinerary_list.append(
                            dict(name=participant.name, itinerary=itinerary)
                        )
                    else:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=transit_response_json,
                        )
                else:
                    # tmap 에러메시지일 경우
                    raise HTTPException(
                        status_code=response.status_code, detail=transit_response_json
                    )
        else:
            raise HTTPException(
                status_code=response.status_code, detail=transit_response_json
            )

    response = {
        "station_name": station_name,
        "address_name": address_name,
        "end_x": end_x,
        "end_y": end_y,
        "share_key": str(uuid.uuid4()),
        "itinerary": itinerary_list,
    }
    redis_config.set(response.get("share_key"), json.dumps(response))

    return response


def get_location_point(query):
    share_key = query.share_key
    share_key_exists_in_redis = redis_config.get(share_key)

    if share_key_exists_in_redis is None:
        raise HTTPException(status_code=404, detail="Not Found")
    else:
        response = json.loads(share_key_exists_in_redis.decode("utf-8"))
        return response


def get_point_place(path, query):
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

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    response = requests.get(url, headers=headers, params=query).json()
    return response


def post_popular_meeting_location():
    KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
    db = next(get_db())
    current_time = datetime.now()
    print(f"popular meeting location update trigger start : {current_time}")

    open_api_data = open_api.call_open_data_api_popular_subway()
    popular_subway_redis_data = redis_config.get("popular_subway")

    if popular_subway_redis_data is None:
        redis_config.set("popular_subway", json.dumps(open_api_data))
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
        redis_config.set("popular_subway", json.dumps(exists_data + added_data))

    popular_subway_in_redis = json.loads(
        redis_config.get("popular_subway").decode("utf-8")
    )
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
