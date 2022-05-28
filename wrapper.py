from github.GithubException import RateLimitExceededException
from datetime import datetime
from math import ceil
from time import sleep
import logging


# Get the logger specified in the file
logger = logging.getLogger("mappers")

def rate_handler(func, *args, **kwargs):
    try:
        results = func(*args, **kwargs)
    except RateLimitExceededException as limit:
        retry_time = limit.headers.get("x-ratelimit-reset")
        if retry_time == None:
            retry_time = limit.headers.get("Retry-After")
        else:
            current_time = datetime.now()
            retry_time = ceil(int(retry_time) - current_time.timestamp())
        if retry_time == None:
            logger.error("Rate limit hit and could not detect retry after header")
            logger.error(limit.headers)
            raise limit
        retry_time += 10
        logger.warn(f"Rate Limit hit waiting for {retry_time/60} minutes")
        sleep(retry_time)
        results = func(*args, **kwargs)
    return results
