import math

import requests
from decouple import config

from app.core.setting import settings
from app.crud import location
from app.models.location import PopularMeetingLocation
from app.services.temp_point_location import target


def calculate_centroid(vertices):
    total_weight = 0
    centroid_x = 0
    centroid_y = 0

    for vertex in vertices.participant:
        x, y = float(vertex.x), float(vertex.y)
        total_weight += 1
        centroid_x += x
        centroid_y += y

    centroid_x /= total_weight
    centroid_y /= total_weight

    return centroid_x, centroid_y


def calculate_distance(centroid_point, place_list):
    centroid_point_x, centroid_point_y = centroid_point
    largest_distance = float("inf")
    res = None

    for place_data in place_list:
        place_point_x = float(place_data["x"])
        place_point_y = float(place_data["y"])
        current_distance = math.sqrt(
            (centroid_point_x - place_point_x) ** 2
            + (centroid_point_y - place_point_y) ** 2
        )
        if current_distance < largest_distance:
            largest_distance = current_distance
            res = place_data
    return res


def post_location_point(body):
    place_list = target.values()

    centroid_point = calculate_centroid(body)
    location_data = calculate_distance(centroid_point, place_list)

    station_name = location_data["place_name"]
    address_name = location_data["road_address_name"]
    point_x = location_data["x"]
    point_y = location_data["y"]

    url = "https://apis.openapi.sk.com/transit/routes"
    headers = {
        "accept": "application/json",
        "appKey": "e8wHh2tya84M88aReEpXCa5XTQf3xgo01aZG39k5",
        "content-type": "application/json",
    }

    itinerary_list = list()
    for participant in body.participant:
        x, y = float(participant.x), float(participant.y)
        data = {
            "startX": x,
            "startY": y,
            "endX": point_x,
            "endY": point_y,
            "format": "json",
            "count": 10,
            "searchDttm": "202301011200",
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            # Successful request
            """
            출발주소는 상관업고
            중간지점 역을 찾아서
            출발주소와 중간역을 리턴 (워크 to 워크)
            우선순위는 지하철
            지하철 데이터가 없을경우엔
            최단시간으로 제공
            """

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

            itinerary_list.append(dict(name=participant.name, itinerary=itinerary))
        else:
            # Failed request
            print(f"Error: {response.status_code}, {response.text}")

    response = {
        "station_name": station_name,
        "address_name": address_name,
        "x": point_x,
        "y": point_y,
        "itinerary": itinerary_list,
    }
    return response


def get_location_point_place(q):
    REST_API_KEY = config("KAKAO_REST_API_KEY")
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {REST_API_KEY}"}

    q = dict(q)
    if q["category_name"] in ["food", "drink"]:
        q.update(category_group_code="FD6")
    if q["category_name"] == "cafe":
        q.update(category_group_code="CE7")

    response = requests.get(url, headers=headers, params=q).json()
    return response


def post_popular_meeting_location(db):
    KAKAO_REST_API_KEY = settings.KAKAO_REST_API_KEY
    TARGET_STATION = [
        "가산디지털단지역",
        "강남역",
        "고속터미널역",
        "교대역",
        "천호역",
        "양재역",
        "군자역",
        "왕십리역",
        "신논현역·논현역",
        "홍대입구역(2호선)",
        "선릉역",
        "신도림역",
        "연신내역",
        "동대문역",
        "건대입구역",
        "충정로역",
        "사당역",
        "혜화역",
        "용산역",
        "뚝섬역",
        "신촌·이대역",
        "서울대입구역",
        "성신여대입구역",
        "총신대입구(이수)역",
        "역삼역",
        "구로디지털단지역",
        "합정역",
        "장한평역",
        "이태원역",
        "미아사거리역",
        "회기역",
        "오목교역·목동운동장",
        "발산역",
        "신림역",
        "서울역",
        "수유역",
        "서울식물원·마곡나루역",
        "구로역",
        "삼각지역",
        "고덕역",
        "대림역",
        "남구로역",
        "장지역",
        "북한산우이역",
    ]

    popular_meeting_location_obj = []
    for station in TARGET_STATION:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {"query": station}
        response = requests.get(url, headers=headers, params=params)

        for kakao_data in response.json()["documents"]:
            if kakao_data["category_group_name"] == "지하철역":
                location_obj = PopularMeetingLocation(
                    name=station,
                    type="station",
                    url=kakao_data["place_url"],
                    address=kakao_data["road_address_name"],
                    location_x=kakao_data["x"],
                    location_y=kakao_data["y"],
                )
                popular_meeting_location_obj.append(location_obj)
                break

    location.create_popular_meeting_location(db, popular_meeting_location_obj)
    response = {
        "msg": "인기 있는 장소 생성 완료",
    }
    return response
