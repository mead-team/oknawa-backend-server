import requests
from decouple import config


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
