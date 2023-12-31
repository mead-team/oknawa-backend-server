import redis

from app.core.setting import settings


def get_redis():
    REDIS_HOST = settings.REDIS_HOST
    REDIS_PORT = settings.REDIS_PORT
    REDIS_DATABASE = settings.REDIS_DATABASE
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE)
