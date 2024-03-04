import polyline
from collections import defaultdict
from urllib.parse import quote

import requests
from fastapi import HTTPException

from app.core.setting import settings
from app.core.util import route_util


def call_open_data_api_popular_subway():
    url = f"{settings.OPEN_DATA_API_URL}/json/CardSubwayStatsNew/1/1000/20231201"
    api_response = requests.get(url).json().get("CardSubwayStatsNew").get("row")
    total_passenger = defaultdict(lambda: {"RIDE_PASGR_NUM": 0, "ALIGHT_PASGR_NUM": 0})

    for subway in api_response:
        subway_name = subway["SUB_STA_NM"]
        total_passenger[subway_name]["RIDE_PASGR_NUM"] += subway["RIDE_PASGR_NUM"]
        total_passenger[subway_name]["ALIGHT_PASGR_NUM"] += subway["ALIGHT_PASGR_NUM"]

    subway_list = [
        {
            "subway_name": subway_name,
            "total_passenger": passenger["RIDE_PASGR_NUM"]
            + passenger["ALIGHT_PASGR_NUM"],
        }
        for subway_name, passenger in total_passenger.items()
    ]
    sorted_subway_list = sorted(
        subway_list, key=lambda x: x["total_passenger"], reverse=True
    )[:80]

    for subway in sorted_subway_list:
        subway["subway_name"] = subway["subway_name"].split("(")[0].strip()
        if not subway["subway_name"].endswith("역"):
            subway["subway_name"] += "역"

    return sorted_subway_list


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


def call_googlemap_api_participant_itinerary(body, center_location_data):
    directions_url = f"{settings.GOOGLE_API_URL}/directions/v2:computeRoutes"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': f"{settings.GOOGLE_API_KEY}",
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline' # 반환필드 선택
    }

    itinerary_list = []
    for participant in body.participant:
        itinerary = dict()
        origin_latitude = participant.start_y
        origin_longitude = participant.start_x
        destination_latitude = center_location_data.location_y
        destination_longitude = center_location_data.location_x

        origin = {"location": {"latLng": dict(latitude=origin_latitude, longitude=origin_longitude)}}
        destination = {"location": {"latLng": dict(latitude=destination_latitude, longitude=destination_longitude)}}
        
        source_and_target = {
            "origin": origin,
            "destination": destination,
            "travelMode": "TRANSIT",
            "transitPreferences": { "allowedTravelModes": ["SUBWAY"]}, # 선호 대중교통
            "languageCode": "ko-KR"
        }
        response = requests.post(
            directions_url,
            headers=headers,
            json=source_and_target,
        )
        response_route = response.json().get("routes")[0]
        duration = int(response_route.get("duration")[:-1])
        decoded_polyline = polyline.decode(response_route.get("polyline").get("encodedPolyline"))
        total_polyline = [{"lng": lng, "lat": lat} for lat, lng in decoded_polyline]
        itinerary.update(total_polyline=total_polyline, totalTime=duration)
        itinerary_list.append(
            dict(
                name=participant.name,
                region_name=participant.region_name,
                itinerary=itinerary,
            )
        )

    return itinerary_list
