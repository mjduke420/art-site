"""Public, Flickr-style browsing: home album grid, albums, photo detail, about."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Album, BlogPost, Photo
from ..templating import templates

router = APIRouter()


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    albums = db.scalars(select(Album).order_by(Album.sort_order, Album.id)).all()
    recent_posts = db.scalars(
        select(BlogPost)
        .where(BlogPost.published.is_(True))
        .order_by(BlogPost.created_at.desc())
        .limit(3)
    ).all()
    return templates.TemplateResponse(
        "public/home.html",
        {"request": request, "albums": albums, "recent_posts": recent_posts},
    )


@router.get("/albums/{slug}")
def album_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    album = db.scalar(select(Album).where(Album.slug == slug))
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return templates.TemplateResponse(
        "public/album.html", {"request": request, "album": album}
    )


@router.get("/photo/{photo_id}")
def photo_detail(photo_id: int, request: Request, db: Session = Depends(get_db)):
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return templates.TemplateResponse(
        "public/photo.html", {"request": request, "photo": photo}
    )


@router.get("/about")
def about(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("public/about.html", {"request": request})
