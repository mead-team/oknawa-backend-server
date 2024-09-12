import asyncio
from collections import defaultdict
from urllib.parse import quote

import aiohttp
import polyline
import requests
from fastapi import HTTPException

from app.core.setting import settings
from app.core.util import aiohttp_util, route_util


def call_open_data_api_popular_subway():
    url = f"{settings.OPEN_DATA_API_URL}/json/CardSubwayStatsNew/1/1000/20231201"
    api_response = requests.get(url).json().get("CardSubwayStatsNew").get("row")
    total_passenger = defaultdict(lambda: {"GTON_TNOPE": 0, "GTOFF_TNOPE": 0})

    for subway in api_response:
        subway_name = subway["SBWY_STNS_NM"]
        total_passenger[subway_name]["GTON_TNOPE"] += subway["GTON_TNOPE"]
        total_passenger[subway_name]["GTOFF_TNOPE"] += subway["GTOFF_TNOPE"]

    subway_list = [
        {
            "subway_name": subway_name,
            "total_passenger": passenger["GTON_TNOPE"] + passenger["GTOFF_TNOPE"],
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
        "Content-Type": "application/json",
        "X-Goog-Api-Key": f"{settings.GOOGLE_API_KEY}",
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",  # 반환필드 선택
    }

    itinerary_list = []
    for participant in body.participant:
        itinerary = dict()
        origin_latitude = participant.start_y
        origin_longitude = participant.start_x
        destination_latitude = center_location_data.location_y
        destination_longitude = center_location_data.location_x

        origin = {
            "location": {
                "latLng": dict(latitude=origin_latitude, longitude=origin_longitude)
            }
        }
        destination = {
            "location": {
                "latLng": dict(
                    latitude=destination_latitude, longitude=destination_longitude
                )
            }
        }

        source_and_target = {
            "origin": origin,
            "destination": destination,
            "travelMode": "TRANSIT",
            "transitPreferences": {"allowedTravelModes": ["SUBWAY"]},  # 선호 대중교통
            "languageCode": "ko-KR",
        }
        response = requests.post(
            directions_url,
            headers=headers,
            json=source_and_target,
        )
        response_route = response.json().get("routes")[0]
        duration = int(response_route.get("duration")[:-1])
        decoded_polyline = polyline.decode(
            response_route.get("polyline").get("encodedPolyline")
        )
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


async def tmap_api_post_and_parse(
    session, transit_url, pedestrian_url, headers, source_and_target
):
    idx = source_and_target.pop("idx")
    name = source_and_target.pop("name")
    region_name = source_and_target.pop("region_name")
    station_name = source_and_target.pop("station_name")

    itinerary = {
        "idx": idx,
        "name": name,
        "region_name": region_name,
    }

    transit_response_status_code, transit_response_json = await aiohttp_util.post(
        session, transit_url, headers=headers, json=source_and_target
    )

    if transit_response_status_code != 200:
        raise HTTPException(
            status_code=transit_response_status_code,
            detail=transit_response_json,
        )

    if transit_response_json.get("metaData"):
        extracted_itinerary = route_util.extract_itinerary_list(transit_response_json)
        total_polyline = route_util.extract_polyline(extracted_itinerary)
        extracted_itinerary.update(total_polyline=total_polyline)
        itinerary["itinerary"] = extracted_itinerary
    else:
        if transit_response_json.get("result", {}).get("status") == 11:
            # 거리가 너무 가까운경우
            start_name = quote(name, encoding="utf-8")
            end_name = quote(station_name, encoding="utf-8")
            source_and_target.update(startName=start_name, endName=end_name)
            pedestrian_response_status_code, pedestrian_response_json = (
                await aiohttp_util.post(
                    session, pedestrian_url, headers=headers, json=source_and_target
                )
            )
            if pedestrian_response_status_code != 200:
                raise HTTPException(
                    status_code=pedestrian_response_status_code,
                    detail=pedestrian_response_json,
                )

            extracted_itinerary = {}
            total_polyline = []
            features = pedestrian_response_json.get("features")
            for feature in features:
                properties = feature.get("properties")
                if properties.get("pointType") == "SP":
                    extracted_itinerary.update(totalTime=properties.get("totalTime"))
                    lng, lat = feature.get("geometry").get("coordinates")
                    total_polyline.append({"lng": lng, "lat": lat})
                if not properties.get("pointType"):
                    coordinates = feature.get("geometry").get("coordinates")
                    for coordinate in coordinates[1:]:
                        lng, lat = coordinate
                        total_polyline.append({"lng": lng, "lat": lat})
            extracted_itinerary.update(total_polyline=total_polyline)
            itinerary["itinerary"] = extracted_itinerary
        else:
            raise HTTPException(
                status_code=transit_response_status_code,
                detail=transit_response_json,
            )

    return itinerary


async def call_tmap_api_participant_itineraries(body, center_location_data_list):
    transit_url = f"{settings.TMAP_API_URL}/transit/routes"
    pedestrian_url = f"{settings.TMAP_API_URL}/tmap/routes/pedestrian?version=1"
    headers = {"appKey": f"{settings.TMAP_REST_API_KEY}"}

    station_info_list = []
    for idx, center_location_tuple in enumerate(center_location_data_list):
        center_location_data = center_location_tuple[1]
        station_info = {
            "station_name": center_location_data.name,
            "address_name": center_location_data.address,
            "end_x": center_location_data.location_x,
            "end_y": center_location_data.location_y,
            "itinerary": [],
        }

        source_and_target_list = [
            {
                "startX": participant.start_x,
                "startY": participant.start_y,
                "endX": center_location_data.location_x,
                "endY": center_location_data.location_y,
                "name": participant.name,
                "region_name": participant.region_name,
                "station_name": center_location_data.name,
                "idx": idx,
            }
            for participant in body.participant
        ]
        station_info["source_and_target_list"] = source_and_target_list
        station_info_list.append(station_info)

    async with aiohttp.ClientSession() as session:
        post_and_parse_tasks = []
        for station_info in station_info_list:
            source_and_target_list = station_info.pop("source_and_target_list")
            for source_and_target in source_and_target_list:
                post_and_parse_tasks.append(
                    tmap_api_post_and_parse(
                        session, transit_url, pedestrian_url, headers, source_and_target
                    )
                )

        itineraries = await asyncio.gather(*post_and_parse_tasks)

    for itinerary in itineraries:
        idx = itinerary.pop("idx")
        station_info_list[idx]["itinerary"].append(itinerary)

    return station_info_list


async def googlemap_api_post_and_parse(
    session, directions_url, headers, source_and_target
):
    idx = source_and_target.pop("idx")
    name = source_and_target.pop("name")
    region_name = source_and_target.pop("region_name")

    status_code, response = await aiohttp_util.post(
        session, directions_url, headers=headers, json=source_and_target
    )

    if status_code != 200:
        raise HTTPException(
            status_code=status_code,
            detail=response,
        )

    routes = response.get("routes")[0]
    duration = int(routes.get("duration")[:-1])
    decoded_polyline = polyline.decode(routes.get("polyline").get("encodedPolyline"))
    total_polyline = [{"lng": lng, "lat": lat} for lat, lng in decoded_polyline]

    itinerary = {
        "idx": idx,
        "name": name,
        "region_name": region_name,
        "itinerary": {"total_polyline": total_polyline, "totalTime": duration},
    }
    return itinerary


async def call_googlemap_api_participant_itineraries(body, center_location_data_list):
    directions_url = f"{settings.GOOGLE_API_URL}/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": f"{settings.GOOGLE_API_KEY}",
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
    }

    station_info_list = []
    for idx, center_location_tuple in enumerate(center_location_data_list):
        center_location_data = center_location_tuple[1]
        station_info = {
            "station_name": center_location_data.name,
            "address_name": center_location_data.address,
            "end_x": center_location_data.location_x,
            "end_y": center_location_data.location_y,
            "itinerary": [],
        }

        source_and_target_list = [
            {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": participant.start_y,
                            "longitude": participant.start_x,
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": center_location_data.location_y,
                            "longitude": center_location_data.location_x,
                        }
                    }
                },
                "travelMode": "TRANSIT",
                "transitPreferences": {"allowedTravelModes": ["SUBWAY"]},
                "languageCode": "ko-KR",
                "name": participant.name,
                "region_name": participant.region_name,
                "idx": idx,
            }
            for participant in body.participant
        ]
        station_info["source_and_target_list"] = source_and_target_list
        station_info_list.append(station_info)

    async with aiohttp.ClientSession() as session:
        post_and_parse_tasks = []
        for station_info in station_info_list:
            source_and_target_list = station_info.pop("source_and_target_list")
            for source_and_target in source_and_target_list:
                post_and_parse_tasks.append(
                    googlemap_api_post_and_parse(
                        session, directions_url, headers, source_and_target
                    )
                )

        itineraries = await asyncio.gather(*post_and_parse_tasks)

    for itinerary in itineraries:
        idx = itinerary.pop("idx")
        station_info_list[idx]["itinerary"].append(itinerary)

    return station_info_list
