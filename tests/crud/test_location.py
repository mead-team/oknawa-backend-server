def test_get_popular_meeting_location_all(db):
    from app.crud.location import get_popular_meeting_location_all

    place_data = get_popular_meeting_location_all(db)
    assert place_data


def test_get_popular_meeting_location_first(db):
    from app.crud.location import get_popular_meeting_location_first

    station_name = "강남역 2호선"
    location_x = "127.02800140627488"
    location_y = "37.49808633653005"
    success_place_data = get_popular_meeting_location_first(
        db, station_name, location_x, location_y
    )
    assert success_place_data


def test_delete_popular_meeting_location(db):
    from datetime import datetime

    from app.crud.location import delete_popular_meeting_location

    current_time = datetime.now()
    delete_popular_meeting_location(db, current_time)
