import time
import logging
from fastapi import HTTPException
import redis
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback
_in_memory_daily_cost = 0.0
_in_memory_reset_day = ""

def check_and_record_cost(input_tokens: int, output_tokens: int):
    """
    Tracks daily cost and enforces budget. Uses Redis if available.
    """
    global _in_memory_daily_cost, _in_memory_reset_day
    
    today = time.strftime("%Y-%m-%d")
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    
    if settings.redis_url:
        try:
            r = redis.from_url(settings.redis_url, decode_responses=True)
            redis_key = f"daily_cost:{today}"
            
            # Atomic increment
            # Use float increment in Redis
            current_cost = float(r.get(redis_key) or 0)
            
            if current_cost >= settings.daily_budget_usd:
                raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
            
            new_cost = r.incrbyfloat(redis_key, cost)
            # Set expiry (2 days)
            r.expire(redis_key, 172800)
            return new_cost
        except redis.RedisError as e:
            logger.error(f"Redis error in cost guard: {e}. Falling back to in-memory.")

    # In-memory fallback
    if today != _in_memory_reset_day:
        _in_memory_daily_cost = 0.0
        _in_memory_reset_day = today
        
    if _in_memory_daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
    
    _in_memory_daily_cost += cost
    return _in_memory_daily_cost

def get_current_cost():
    """Returns the current daily cost."""
    today = time.strftime("%Y-%m-%d")
    if settings.redis_url:
        try:
            r = redis.from_url(settings.redis_url, decode_responses=True)
            return float(r.get(f"daily_cost:{today}") or 0)
        except:
            pass
    return _in_memory_daily_cost
