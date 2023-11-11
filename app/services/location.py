import requests
from decouple import config


def hotplace(q):
    REST_API_KEY = config("KAKAO_REST_API_KEY")
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {
        "Authorization": f"KakaoAK {REST_API_KEY}"
    }
    response = requests.get(url, headers=headers, params=q).json()
    
    return response