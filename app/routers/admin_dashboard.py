"""Admin dashboard landing page."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Album, BlogPost, Photo, User
from ..security import require_admin
from ..templating import templates

router = APIRouter()


@router.get("/admin")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    stats = {
        "albums": db.scalar(select(func.count()).select_from(Album)),
        "photos": db.scalar(select(func.count()).select_from(Photo)),
        "posts": db.scalar(select(func.count()).select_from(BlogPost)),
    }
    recent_albums = db.scalars(
        select(Album).order_by(Album.created_at.desc()).limit(5)
    ).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": user, "stats": stats, "recent_albums": recent_albums},
    )
