import json
import time
from typing import Any, Dict, Optional
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from app.core.config import settings
from app.core.logging import logger
from app.core.redis import get_redis_client

JWKS_CACHE_KEY = "jwks:clerk"
JWKS_CACHE_TTL = 3600  # 1 hour


class SecurityError(Exception):
    def __init__(self, message: str, code: str = "UNAUTHORIZED"):
        self.message = message
        self.code = code
        super().__init__(message)


async def get_clerk_jwks() -> Dict[str, Any]:
    """Fetch and cache Clerk JWKS."""
    redis = await get_redis_client()
    cached = await redis.get(JWKS_CACHE_KEY)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    jwks_url = settings.CLERK_JWKS_URL or "https://api.clerk.com/v1/jwks"
    headers = {}
    if settings.CLERK_SECRET_KEY:
        headers["Authorization"] = f"Bearer {settings.CLERK_SECRET_KEY}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(jwks_url, headers=headers)
            if resp.status_code == 200:
                jwks_data = resp.json()
                await redis.set(JWKS_CACHE_KEY, json.dumps(jwks_data), ex=JWKS_CACHE_TTL)
                return jwks_data
            else:
                logger.error("Failed to fetch JWKS from Clerk: status %d", resp.status_code)
    except Exception as e:
        logger.error("Exception fetching JWKS: %s", e)

    return {"keys": []}


async def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verifies a Clerk JWT.
    Returns the decoded token claims if valid, raises SecurityError otherwise.
    """
    if not token:
        raise SecurityError("Missing authorization token")

    # Support dev token bypass for testing/mocking if explicitly enabled
    if settings.ALLOW_DEV_AUTH_BYPASS and token.startswith("dev-token-"):
        # Format: dev-token-{role}-{clerk_id}
        parts = token.split("-")
        role = parts[2] if len(parts) > 2 else "student"
        clerk_id = parts[3] if len(parts) > 3 else f"user_{role}"
        return {
            "sub": clerk_id,
            "role": role,
            "public_metadata": {"role": role},
            "email": f"{role}@sbuniversity.edu",
            "name": f"Dev {role.capitalize()}",
        }

    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        raise SecurityError(f"Invalid token header: {str(e)}")

    kid = unverified_header.get("kid")
    if not kid:
        # Check if unverified token can be decoded in dev mode if keys are unavailable
        if settings.DEBUG and not settings.is_production:
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                return claims
            except Exception:
                pass
        raise SecurityError("Token missing key ID (kid)")

    jwks = await get_clerk_jwks()
    keys = jwks.get("keys", [])
    matching_key = next((k for k in keys if k.get("kid") == kid), None)

    if not matching_key:
        # Try refreshing JWKS once
        redis = await get_redis_client()
        await redis.delete(JWKS_CACHE_KEY)
        jwks = await get_clerk_jwks()
        keys = jwks.get("keys", [])
        matching_key = next((k for k in keys if k.get("kid") == kid), None)

    if not matching_key:
        if settings.DEBUG and not settings.is_production:
            logger.warning("JWKS key not found; decoding without signature verification in DEBUG mode")
            return jwt.decode(token, options={"verify_signature": False})
        raise SecurityError("Unable to verify token signature: public key not found")

    public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))

    decode_kwargs: Dict[str, Any] = {
        "algorithms": ["RS256"],
        "options": {"verify_exp": True},
    }
    if settings.CLERK_ISSUER:
        decode_kwargs["issuer"] = settings.CLERK_ISSUER

    try:
        payload = jwt.decode(token, public_key, **decode_kwargs)
        return payload
    except jwt.ExpiredSignatureError:
        raise SecurityError("Token has expired", code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError as e:
        raise SecurityError(f"Invalid token: {str(e)}", code="INVALID_TOKEN")
