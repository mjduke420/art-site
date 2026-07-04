"""FastAPI application entrypoint: middleware, mounts, startup seeding, routes."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import models  # noqa: F401  (registers tables on Base.metadata)
from .config import get_settings
from .database import Base, SessionLocal, engine
from .routers import (
    admin_albums,
    admin_auth,
    admin_blog,
    admin_dashboard,
    admin_photos,
    admin_settings,
    blog,
    public,
)
from .security import NotAuthenticatedError
from .services import seed, site

logger = logging.getLogger("portfolio")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed.initialize(db)
    finally:
        db.close()
    if settings.uses_insecure_defaults:
        logger.warning(
            "SECURITY: SECRET_KEY and/or ADMIN_PASSWORD are still default values. "
            "Set them via environment variables before exposing this site."
        )
    yield


app = FastAPI(
    title=settings.site_title,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
    max_age=60 * 60 * 24 * 14,
)

# Static + uploaded media (uploads dir must exist before mounting).
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def attach_site_settings(request: Request, call_next):
    """Expose editable site settings to every template via request.state.site."""
    db = SessionLocal()
    try:
        request.state.site = site.get_site_settings(db)
    finally:
        db.close()
    return await call_next(request)


@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedError):
    return RedirectResponse("/admin/login", status_code=303)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


for router in (
    public.router,
    blog.router,
    admin_auth.router,
    admin_dashboard.router,
    admin_albums.router,
    admin_photos.router,
    admin_blog.router,
    admin_settings.router,
):
    app.include_router(router)
