import math

import requests

from app.core.setting import settings
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


def calculate_distance(centroid_point, place_data):
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

    for place in place_data:
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
    centroid_point = calculate_centroid(body.dict())
    place_data = location.get_popular_meeting_location(db)

    location_data = calculate_distance(centroid_point, place_data)
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

    query = query.dict()
    if path == "food":
        query.update(category_group_code="FD6", query="음식점")
    elif path == "drink":
        query.update(category_group_code="FD6", query="술집")
    elif path == "cafe":
        query.update(category_group_code="CE7", query="카페")

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    response = requests.get(url, headers=headers, params=query).json()
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
