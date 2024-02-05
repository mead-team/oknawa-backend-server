import math


def get_center_coordinates(body):
    """n개의 좌표의 중간지점 계산, 각 연속된 2D(Dimension) 좌표의 평균을 계산

    Args:
        body (obj): /point의 request로 받은 유저별 좌표

    Returns:
        tuple: (중간지점x좌표, 중간지점y좌표)
    """
    center_x = 0
    center_y = 0
    participant = body.get("participant")

    for vertex in participant:
        x, y = vertex.get("start_x"), vertex.get("start_y")
        center_x += x
        center_y += y
    center_x /= len(participant)
    center_y /= len(participant)
    center_coordinates = (center_x, center_y)

    return center_coordinates


def get_center_location(center_coordinates, popular_location_in_db, priority):
    """중간지점좌표와 인기있는역의 거리계산후 가장가까운 역 리턴

    Args:
        center_coordinates (tuple): (중간지점x좌표, 중간지점y좌표)
        popular_location_in_db (obj): db의 인기있는역 데이터
        priority(int): n번째로 가까운 지역

    Returns:
        dict: 인기 있는역 데이터의 요소 중 중간지점좌표와 n번째로 가까운 지역
    """
    center_x, center_y = center_coordinates
    location = []

    for popular_location in popular_location_in_db:
        location_x = float(popular_location.location_x)
        location_y = float(popular_location.location_y)
        current_distance = math.sqrt(
            (center_x - location_x) ** 2 + (center_y - location_y) ** 2
        )
        location.append((current_distance, popular_location))

    sorted_locations = sorted(location, key=lambda x: x[0])

    return sorted_locations[priority][1]
