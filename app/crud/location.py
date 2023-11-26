def create_popular_meeting_location(db, popular_meeting_location_obj):
    db.add_all(popular_meeting_location_obj)
    db.commit()
