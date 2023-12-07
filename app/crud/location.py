from datetime import datetime

from app.models.location import PopularMeetingLocation


def create_popular_meeting_location(db, popular_meeting_location_obj):
    db.add_all(popular_meeting_location_obj)
    db.commit()


def get_popular_meeting_location_all(db):
    place_data = (
        db.query(PopularMeetingLocation)
        .filter(PopularMeetingLocation.deleted_at.is_(None))
        .all()
    )
    return place_data


def get_popular_meeting_location_first(db, station_name, location_x, location_y):
    place_data = (
        db.query(PopularMeetingLocation)
        .filter(
            PopularMeetingLocation.name == station_name,
            PopularMeetingLocation.location_x == location_x,
            PopularMeetingLocation.location_y == location_y,
            PopularMeetingLocation.deleted_at.is_(None),
        )
        .first()
    )
    return place_data


def delete_popular_meeting_location(db, current_time):
    today = datetime.now()
    start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    place_data = (
        db.query(PopularMeetingLocation)
        .filter(
            PopularMeetingLocation.updated_at < start_of_today,
            PopularMeetingLocation.deleted_at.is_(None),
        )
        .all()
    )

    for data in place_data:
        data.deleted_at = current_time
    db.commit()

    return place_data
