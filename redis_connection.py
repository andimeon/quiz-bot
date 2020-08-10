import redis
import os

from dotenv import load_dotenv

load_dotenv()


def get_database_access():
    return redis.Redis(
        host=os.getenv("REDIS_URL"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        charset="utf-8",
        decode_responses=True,
    )