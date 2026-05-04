from redis import Redis
from redis.exceptions import RedisError
from api.core.settings import settings

redis_client = Redis.from_url(url=settings.REDIS_URL,decode_responses=True,
                              socket_timeout=2.0, socket_connect_timeout=2.0, health_check_interval=30)

def ping_redis()-> bool:
    try:
        return bool ( redis_client.ping())
    except RedisError:
        return False 
