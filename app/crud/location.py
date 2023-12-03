from app.models.location import PopularMeetingLocation


def create_popular_meeting_location(db, popular_meeting_location_obj):
    db.add_all(popular_meeting_location_obj)
    db.commit()


def get_popular_meeting_location(db):
    place_data = (
        db.query(PopularMeetingLocation)
        .filter(PopularMeetingLocation.deleted_at == None)
        .all()
    )
    return place_data
