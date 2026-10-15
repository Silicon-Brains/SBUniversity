import asyncio
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.redis import close_redis_client, get_redis_client
from app.db.session import AsyncSessionLocal
from app.repositories.exam_repository import ExamRepository
from app.services.exam_service import ExamService
from app.services.ranking_service import RankingService


async def periodic_expired_attempts_sweeper():
    """Background task to auto-submit expired in-progress attempts."""
    while True:
        try:
            await asyncio.sleep(60)  # check every minute
            async with AsyncSessionLocal() as session:
                exam_repo = ExamRepository(session)
                expired_attempts = await exam_repo.list_expired_in_progress_attempts()
                if expired_attempts:
                    logger.info("Sweeper found %d expired attempts to auto-submit", len(expired_attempts))
                    exam_service = ExamService(session)
                    for att in expired_attempts:
                        try:
                            await exam_service.submit_attempt(att.id, att.student_id, is_auto=True)
                            logger.info("Auto-submitted expired attempt %s", att.id)
                        except Exception as e:
                            logger.error("Error auto-submitting attempt %s: %s", att.id, e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Exception in periodic sweeper: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting %s in %s mode...", settings.APP_NAME, settings.APP_ENV)

    # Initialize Redis connection
    await get_redis_client()

    # Rebuild cold-start leaderboard if needed
    try:
        async with AsyncSessionLocal() as session:
            ranking_svc = RankingService(session)
            await ranking_svc.rebuild_all_scores()
    except Exception as e:
        logger.warning("Initial leaderboard rebuild skipped or failed (DB may not be migrated yet): %s", e)

    # Start background sweeper
    sweeper_task = asyncio.create_task(periodic_expired_attempts_sweeper())

    yield

    # Shutdown
    sweeper_task.cancel()
    try:
        await sweeper_task
    except asyncio.CancelledError:
        pass
    await close_redis_client()
    logger.info("Shutdown complete for %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Full Production Ready Backend for SBUniversity",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers (Standard error shape from Docs/architecture.md & Docs/rules.md)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please contact support.",
                "details": str(exc) if settings.DEBUG else None,
            }
        },
    )


# Health Checks
@app.get("/health")
@app.get(f"{settings.API_V1_PREFIX}/health")
async def health_check():
    db_ok = False
    redis_ok = False

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    try:
        redis = await get_redis_client()
        redis_ok = await redis.ping()
    except Exception:
        redis_ok = False

    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
