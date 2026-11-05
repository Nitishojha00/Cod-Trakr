import os

import redis.asyncio as redis_async
from dotenv import load_dotenv

load_dotenv()

redis_client = redis_async.Redis(
    host=os.getenv("REDIS_USER_HOST") or "localhost",
    port=int(os.getenv("REDIS_USER_PORT") or 6379),
    username=os.getenv("REDIS_USER_NAME") or None,
    password=os.getenv("REDIS_USER_PASS") or None,
    decode_responses=True,
)
