"""
Sales Intelligence Platform — Backend (Alpha MVP)
Phase 1: Placeholder entry point. Full implementation in Phase 2.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Sales Intelligence & AI Outreach Platform",
    description="Alpha MVP — Lead management, enrichment, campaigns, AI outreach",
    version="0.1.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "phase": "1"}
