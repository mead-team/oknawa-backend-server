def extract_polyline(itinerary):
    total_polyline = []
    for leg in itinerary.pop("legs"):
        pass_shape = leg.get("passShape")
        linestrings = (
            pass_shape.get("linestring")
            if pass_shape
            else " ".join([step["linestring"] for step in leg["steps"]])
        )

        for linestring in linestrings.split(" "):
            lng, lat = [float(line) for line in linestring.split(",")]
            total_polyline.append(dict(lng=lng, lat=lat))

    return total_polyline


def extract_itinerary_list(transit_response_json):
    subway_list = list(
        filter(
            lambda x: x["pathType"] == 1,
            transit_response_json["metaData"]["plan"]["itineraries"],
        )
    )
    if subway_list:
        itinerary = min(subway_list, key=lambda x: x["totalTime"])
    else:
        itinerary = min(
            transit_response_json["metaData"]["plan"]["itineraries"],
            key=lambda x: x["totalTime"],
        )

    return itinerary
