import json
import math
from datetime import datetime

import requests

from app.core.dependency import get_db
from app.core.redis import redis_config
from app.core.setting import settings
from app.core.util import open_api
from app.crud import location
from app.models.location import PopularMeetingLocation


def calculate_centroid(body):
    """n개의 좌표의 중간지점 계산, 각 연속된 2D(Dimension) 좌표의 평균을 계산

    Args:
        body (obj): /point의 request로 받은 유저별 좌표

    Returns:
        tuple: (중간지점x좌표, 중간지점y좌표)
    """
    centroid_x = 0
    centroid_y = 0
    participant = body.get("participant")

    for vertex in participant:
        x, y = vertex.get("start_x"), vertex.get("start_y")
        centroid_x += x
        centroid_y += y
    centroid_x /= len(participant)
    centroid_y /= len(participant)
    centroid_point = (centroid_x, centroid_y)

    return centroid_point


def calculate_distance(centroid_point, place_data_in_db):
    """중간지점좌표와 인기있는역의 거리계산후 가장가까운 역 리턴

    Args:
        centroid_point (tuple): (중간지점x좌표, 중간지점y좌표)
        place_list (list): temp_point_location의 target dict의 values()

    Returns:
        dict: place_list의 요소 중간지점좌표와 가장가까운 역
    """
    centroid_x, centroid_y = centroid_point
    largest_distance = float("inf")
    location_data = None

    for place in place_data_in_db:
        place_point_x = float(place.location_x)
        place_point_y = float(place.location_y)
        current_distance = math.sqrt(
            (centroid_x - place_point_x) ** 2 + (centroid_y - place_point_y) ** 2
        )
        if current_distance < largest_distance:
            largest_distance = current_distance
            location_data = place
    return location_data


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
    TMAP_REST_API_KEY = settings.TMAP_REST_API_KEY
    centroid_point = calculate_centroid(body.model_dump())
    place_data_in_db = location.get_popular_meeting_location_all(db)

    location_data = calculate_distance(centroid_point, place_data_in_db)
    station_name = location_data.name
    address_name = location_data.address
    end_x = location_data.location_x
    end_y = location_data.location_y

    # Tmap
    url = "https://apis.openapi.sk.com/transit/routes"
    headers = {"appKey": f"{TMAP_REST_API_KEY}"}

    itinerary_list = list()
    for participant in body.participant:
        start_x, start_y = float(participant.start_x), float(participant.start_y)
        response = requests.post(
            url,
            headers=headers,
            json=dict(startX=start_x, startY=start_y, endX=end_x, endY=end_y),
        )

        if response.status_code == 200:
            result = response.json()
            subway_list = list(
                filter(
                    lambda x: x["pathType"] == 1,
                    result["metaData"]["plan"]["itineraries"],
                )
            )
            if subway_list:
                itinerary = min(subway_list, key=lambda x: x["totalTime"])
            else:
                itinerary = min(
                    result["metaData"]["plan"]["itineraries"],
                    key=lambda x: x["totalTime"],
                )
            total_polyline = list()
            for leg in itinerary.pop("legs"):
                if "passShape" in leg.keys():
                    linestrings = leg.pop("passShape").pop("linestring")
                else:
                    linestrings = " ".join(
                        [step.pop("linestring") for step in leg.pop("steps")]
                    )
                linestrings = linestrings.split(" ")

                for linestring in linestrings:
                    lng, lat = [float(line) for line in linestring.split(",")]
                    total_polyline.append(dict(lng=lng, lat=lat))
            itinerary["total_polyline"] = total_polyline
            itinerary_list.append(dict(name=participant.name, itinerary=itinerary))
        else:
            # Failed request
            print(f"Error: {response.status_code}, {response.text}")

    response = {
        "station_name": station_name,
        "address_name": address_name,
        "end_x": end_x,
        "end_y": end_y,
        "itinerary": itinerary_list,
    }
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
