"""API v1 routers."""

from app.api.v1.routers.asistan import router as asistan_router
from app.api.v1.routers.healthz import router as healthz_router

__all__ = ["asistan_router", "healthz_router"]
