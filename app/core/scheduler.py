from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.dependency import get_db
from app.core.redis import get_redis
from app.services import location

scheduler = BackgroundScheduler()
scheduler.add_job(
    location.post_popular_meeting_location,
    CronTrigger(day_of_week="sun", hour=0, minute=0),
    args=[next(get_db()), get_redis()],
)
