from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router
from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware
from app.services.cleanup import cleanup_old_files

settings = get_settings()
settings.ensure_dirs()

app = FastAPI(
    title="AI Rooftop Solar Auditor",
    version="0.1.0",
    description="Meta Hackathon MVP — SAM 3.1 + Muse adapters with mock fallback",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)

app.include_router(router)
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


@app.on_event("startup")
def _cleanup_stale_static() -> None:
    stats = cleanup_old_files(settings)
    if stats["removed"]:
        import logging

        logging.getLogger(__name__).info("startup cleanup removed=%d", stats["removed"])


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Rooftop Solar Auditor",
        "docs": "/docs",
        "health": "/api/health",
    }
