import os
import redis
from rq import Queue

redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

conn = redis.Redis.from_url(redis_url, password=redis_token)
queue = Queue(connection=conn)
