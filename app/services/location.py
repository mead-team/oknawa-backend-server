import math

import requests
from decouple import config

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


def get_location_point(body):
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
