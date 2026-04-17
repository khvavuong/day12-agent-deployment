from fastapi import HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
COOKIE_NAME = "agent_api_key"

def verify_api_key(request: Request, api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to verify API key.
    Priority:
    1) X-API-Key header (for API clients)
    2) HttpOnly cookie (for first-party web UI)
    """
    candidate_key = api_key or request.cookies.get(COOKIE_NAME)
    if not candidate_key or candidate_key != settings.agent_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )
    return candidate_key
