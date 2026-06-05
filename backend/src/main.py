"""
Sales Intelligence Platform — Backend (Alpha MVP)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.analytics.router import router as analytics_router
from src.auth.router import router as auth_router
from src.campaigns.router import messages_router, router as campaigns_router
from src.common.config import get_settings
from src.common.database import engine
from src.common.exceptions import AppException
from src.common.handlers import app_exception_handler
from src.enrichment.router import router as enrichment_router
from src.leads.router import router as leads_router
from src.users.router import router as users_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="Parijat Sales Intelligence Platform",
    description="Lead discovery, enrichment, campaigns, and AI outreach",
    version="0.2.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(leads_router, prefix=settings.api_v1_prefix)
app.include_router(enrichment_router, prefix=settings.api_v1_prefix)
app.include_router(campaigns_router, prefix=settings.api_v1_prefix)
app.include_router(messages_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)

app.add_exception_handler(AppException, app_exception_handler)


@app.get("/health")
async def health_check() -> dict:
    checks: dict[str, str] = {"api": "ok"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
    try:
        import redis

        r = redis.from_url(settings.redis_url)
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
