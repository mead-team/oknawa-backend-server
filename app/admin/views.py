from sqladmin import ModelView
from app.models.location import PopularMeetingLocation

class PopularMeetingLocationAdmin(ModelView, model=PopularMeetingLocation):
    name = "PopularMeetingLocation"
    name_plural = "PopularMeetingLocation"
    icon = "fa-solid fa-book"
    can_create = False
    can_delete = False
    can_edit = False
    column_list = [c.name for c in PopularMeetingLocation.__table__.c]