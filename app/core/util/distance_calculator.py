import math


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


def calculate_distance(centroid_point, place_data_in_db):
    """중간지점좌표와 인기있는역의 거리계산후 가장가까운 역 리턴

    Args:
        centroid_point (tuple): (중간지점x좌표, 중간지점y좌표)
        place_data_in_db (obj): db의 인기있는역 데이터

    Returns:
        dict: place_list의 요소 중간지점좌표와 가장가까운 역
    """
    centroid_x, centroid_y = centroid_point
    largest_distance = float("inf")
    location_data = None

    for place in place_data_in_db:
        place_point_x = float(place.location_x)
        place_point_y = float(place.location_y)
        current_distance = math.sqrt(
            (centroid_x - place_point_x) ** 2 + (centroid_y - place_point_y) ** 2
        )
        if current_distance < largest_distance:
            largest_distance = current_distance
            location_data = place
    return location_data
