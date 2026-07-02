"""FastAPI application entrypoint and startup lifecycle."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.deps import get_embedder, get_qdrant_store
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize critical dependencies once at startup."""
    settings = get_settings()
    configure_logging(settings.app_debug)

    if settings.skip_startup_checks:
        app.state.is_ready = True
        app.state.ready_detail = "startup_checks_skipped"
    else:
        try:
            qdrant_store = get_qdrant_store()
            qdrant_store.is_healthy()

            # Warm model at startup to avoid first-request latency spikes.
            get_embedder()

            app.state.is_ready = True
            app.state.ready_detail = "qdrant_and_embedder_ready"
        except Exception as exc:
            app.state.is_ready = False
            app.state.ready_detail = f"startup_dependency_check_failed: {exc}"

    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.app_debug,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    allowed_origins = [
        origin.strip()
        for origin in settings.cors_allow_origins.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "api_prefix": settings.api_v1_prefix,
        }

    return app


app = create_app()
