import math

import requests
from decouple import config

from app.core.setting import settings
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
    x = location_data["x"]
    y = location_data["y"]

    response = {
        "station_name": station_name,
        "address_name": address_name,
        "x": x,
        "y": y,
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


def get_location_point():
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

    kakao_station_data = {}
    for station in TARGET_STATION:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {"query": station}
        response = requests.get(url, headers=headers, params=params)

        for station_data in response.json()["documents"]:
            if station_data["category_group_name"] == "지하철역":
                print(station_data)
                kakao_station_data[station] = station_data
            else:
                pass

    response = {
        "station_data": kakao_station_data,
    }
    return response
