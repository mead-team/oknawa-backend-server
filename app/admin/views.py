from sqladmin import ModelView
from app.models.location import PopularMeetingLocation

class PopularMeetingLocationAdmin(ModelView, model=PopularMeetingLocation):
    name = "PopularMeetingLocation"
    name_plural = "PopularMeetingLocation"
    icon = "fa-solid fa-book"
    column_list = [c.name for c in PopularMeetingLocation.__table__.c]