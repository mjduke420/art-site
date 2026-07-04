"""Admin: per-photo edits (caption/title), cover selection, deletion, reorder."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Album, Photo, User
from ..security import assert_csrf, require_admin
from ..services import storage

router = APIRouter(prefix="/admin/photos")


def _get_photo_or_404(db: Session, photo_id: int) -> Photo:
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.post("/{photo_id}")
def update_photo(
    photo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    title: str = Form(""),
    caption: str = Form(""),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    photo = _get_photo_or_404(db, photo_id)
    photo.title = title
    photo.caption = caption
    db.commit()
    return RedirectResponse(f"/admin/albums/{photo.album_id}", status_code=303)


@router.post("/{photo_id}/cover")
def set_album_cover(
    photo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    photo = _get_photo_or_404(db, photo_id)
    album = db.get(Album, photo.album_id)
    if album is not None:
        album.cover_photo_id = photo.id
        db.commit()
    return RedirectResponse(f"/admin/albums/{photo.album_id}", status_code=303)


@router.post("/{photo_id}/delete")
def delete_photo(
    photo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    photo = _get_photo_or_404(db, photo_id)
    album_id = photo.album_id
    filename = photo.filename
    album = db.get(Album, album_id)
    if album is not None and album.cover_photo_id == photo.id:
        album.cover_photo_id = None
    db.delete(photo)
    db.commit()
    storage.delete_photo_files(album_id, filename)
    return RedirectResponse(f"/admin/albums/{album_id}", status_code=303)


@router.post("/reorder")
def reorder_photos(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    order: str = Form(...),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    ids = [int(part) for part in order.split(",") if part.strip().isdigit()]
    for position, photo_id in enumerate(ids):
        photo = db.get(Photo, photo_id)
        if photo is not None:
            photo.sort_order = position
    db.commit()
    return JSONResponse({"ok": True})
