import time
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.redis import get_redis_client


class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int, key_prefix: str = "rl"):
        self.limit = requests_limit
        self.window = window_seconds
        self.key_prefix = key_prefix

    async def __call__(self, request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return True

        # Use authenticated user clerk_id or client IP
        identifier = getattr(request.state, "user_id", None)
        if not identifier:
            identifier = request.client.host if request.client else "unknown"

        route = request.url.path
        redis = await get_redis_client()
        key = f"{self.key_prefix}:{route}:{identifier}"

        now = int(time.time())
        window_start = now - self.window

        try:
            # Simple fixed or sliding count
            current_count_str = await redis.get(key)
            current_count = int(current_count_str) if current_count_str else 0

            if current_count >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Try again in {self.window} seconds.",
                            "details": None,
                        }
                    },
                )

            if current_count == 0:
                await redis.set(key, "1", ex=self.window)
            else:
                # Increment
                await redis.set(key, str(current_count + 1), ex=self.window)
        except HTTPException:
            raise
        except Exception:
            # Fail open for reads, but keep going
            return True

        return True
