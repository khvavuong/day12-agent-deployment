import time
import signal
import logging
import json
import os
from typing import Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key, COOKIE_NAME
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost, get_current_cost
from app.agent import agent

# Logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
    }))
    _is_ready = True
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Models for /chat
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[dict] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    reply: str
    tool_used: str
    timestamp: str

# Endpoints
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        response = FileResponse(index_path)
        response.set_cookie(
            key=COOKIE_NAME,
            value=settings.agent_api_key,
            httponly=True,
            secure=settings.environment == "production",
            samesite="strict",
            max_age=60 * 60 * 12,
        )
        return response
    return {"message": "Frontend not found. Check app/static/index.html"}

@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat_endpoint(
    body: ChatRequest,
    _key: str = Depends(verify_api_key),
):
    # 1. Rate Limiting (Stateless)
    check_rate_limit(_key[:8])

    # 2. Budget Check (Stateless)
    input_tokens = len(body.message.split()) * 2
    check_and_record_cost(input_tokens, 0)

    # 3. Agent Processing (Routing + Tools + Safety)
    result = agent.route_request(body.message, body.context)

    # 4. Recording Cost (Output)
    output_tokens = len(result["reply"].split()) * 2
    check_and_record_cost(0, output_tokens)

    return ChatResponse(
        reply=result["reply"],
        tool_used=result["tool_used"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.get("/health", tags=["Operations"])
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}

@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "daily_cost_usd": round(get_current_cost(), 4),
        "daily_budget_usd": settings.daily_budget_usd,
    }

# Graceful Shutdown
def handle_signal(signum, frame):
    logger.info(f"Received signal {signum}")

signal.signal(signal.SIGTERM, handle_signal)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
