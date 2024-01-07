from urllib.parse import quote

import requests
from fastapi import HTTPException

from app.core.setting import settings
from app.core.util import route_util


def call_open_data_api_popular_subway():
    url = f"{settings.OPEN_DATA_API_URL}/json/CardSubwayStatsNew/1/1000/20231201"
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
            "using_date": using_date,
        }
        subway_result.append(subway_data)
    sorted_subway_result = sorted(
        subway_result, key=lambda x: x["total_passenger"], reverse=True
    )[:100]
    return sorted_subway_result


def call_tmap_api_participant_itinerary(body, center_location_data):
    transit_url = f"{settings.TMAP_API_URL}/transit/routes"
    pedestrian_url = f"{settings.TMAP_API_URL}/tmap/routes/pedestrian?version=1"
    headers = {"appKey": f"{settings.TMAP_REST_API_KEY}"}

    itinerary_list = []
    for participant in body.participant:
        source_and_target = dict(
            startX=participant.start_x,
            startY=participant.start_y,
            endX=center_location_data.location_x,
            endY=center_location_data.location_y,
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
                itinerary_list.append(
                    dict(
                        name=participant.name,
                        region_name=participant.region_name,
                        itinerary=itinerary,
                    )
                )
            else:
                if transit_response_json.get("result", {}).get("status") == 11:
                    # 거리가 너무 가까운경우
                    start_name = quote(participant.name, encoding="utf-8")
                    end_name = quote(center_location_data.name, encoding="utf-8")
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
                            dict(
                                name=participant.name,
                                region_name=participant.region_name,
                                itinerary=itinerary,
                            )
                        )
                    else:
                        raise HTTPException(
                            status_code=pedestrian_response.status_code,
                            detail=pedestrian_response.json(),
                        )
                else:
                    # tmap 에러메시지일 경우
                    raise HTTPException(
                        status_code=transit_response.status_code,
                        detail=transit_response.json(),
                    )
        else:
            raise HTTPException(
                status_code=transit_response.status_code, detail=transit_response.json()
            )

    return itinerary_list
