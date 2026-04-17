import time
import logging
from collections import deque, defaultdict
from fastapi import HTTPException
import redis
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback
_in_memory_windows: dict[str, deque] = defaultdict(deque)

def check_rate_limit(key: str):
    """
    Checks rate limit using Redis if available, otherwise falls back to in-memory.
    Algorithm: Sliding Window Counter.
    """
    now = time.time()
    
    if settings.redis_url:
        try:
            r = redis.from_url(settings.redis_url, decode_responses=True)
            pipe = r.pipeline()
            # Redis key for this user's rate limit window
            redis_key = f"rate_limit:{key}"
            
            # Remove entries older than 60 seconds
            pipe.zremrangebyscore(redis_key, 0, now - 60)
            # Get current count
            pipe.zcard(redis_key)
            # Add current request
            pipe.zadd(redis_key, {str(now): now})
            # Set expiry to 60s
            pipe.expire(redis_key, 65)
            
            results = pipe.execute()
            count = results[1]
            
            if count >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                    headers={"Retry-After": "60"},
                )
            return
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiter: {e}. Falling back to in-memory.")
    
    # In-memory fallback
    window = _in_memory_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
        
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min (in-memory)",
            headers={"Retry-After": "60"},
        )
    window.append(now)
