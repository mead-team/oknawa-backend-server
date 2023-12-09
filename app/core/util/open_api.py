import requests

from app.core.setting import settings


def call_open_data_api_popular_subway():
    OPEN_DATA_API_URL = settings.OPEN_DATA_API_URL
    url = f"{OPEN_DATA_API_URL}/json/CardSubwayStatsNew/1/1000/20231201"
    api_response = requests.get(url).json().get("CardSubwayStatsNew").get("row")

    subway_result = []
    for subway in api_response:
        line = subway["LINE_NUM"]
        name = subway["SUB_STA_NM"]
        ride_passenger = subway["RIDE_PASGR_NUM"]
        alight_passenger = subway["ALIGHT_PASGR_NUM"]

        subway_name = f"{line} {name}"
        total_passenger = ride_passenger + alight_passenger
        using_date = subway["USE_DT"]

        subway_data = {
            "subway_name": subway_name,
            "total_passenger": total_passenger,
            "using_date": using_date
        }
        subway_result.append(subway_data)
    sorted_subway_result = sorted(subway_result, key=lambda x: x["total_passenger"], reverse=True)[:100]
    return sorted_subway_result
