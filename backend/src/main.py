"""
Sales Intelligence Platform — Backend (Alpha MVP)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.common.config import get_settings
from src.common.exceptions import AppException
from src.common.handlers import app_exception_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="Sales Intelligence & AI Outreach Platform",
    description="Alpha MVP — Lead management, enrichment, campaigns, AI outreach",
    version="0.1.0-alpha",
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

app.add_exception_handler(AppException, app_exception_handler)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
