"""Admin: album CRUD, photo uploads, and album reordering."""
from __future__ import annotations

import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Album, Photo, User
from ..security import assert_csrf, require_admin
from ..services import images, storage, text
from ..templating import templates

router = APIRouter(prefix="/admin/albums")
settings = get_settings()


def _get_album_or_404(db: Session, album_id: int) -> Album:
    album = db.get(Album, album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return album


@router.get("")
def list_albums(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    albums = db.scalars(select(Album).order_by(Album.sort_order, Album.id)).all()
    return templates.TemplateResponse(
        "admin/albums_list.html", {"request": request, "albums": albums}
    )


@router.get("/new")
def new_album_form(request: Request, user: User = Depends(require_admin)):
    return templates.TemplateResponse(
        "admin/album_form.html", {"request": request, "album": None}
    )


@router.post("")
def create_album(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    title: str = Form(...),
    description: str = Form(""),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    max_order = db.scalar(select(func.max(Album.sort_order))) or 0
    album = Album(
        title=title.strip() or "Untitled album",
        slug=text.unique_slug(db, Album, title),
        description=description,
        sort_order=max_order + 1,
    )
    db.add(album)
    db.commit()
    return RedirectResponse(f"/admin/albums/{album.id}", status_code=303)


@router.get("/{album_id}")
def manage_album(
    album_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    album = _get_album_or_404(db, album_id)
    return templates.TemplateResponse(
        "admin/album_manage.html", {"request": request, "album": album}
    )


@router.post("/{album_id}")
def update_album(
    album_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    title: str = Form(...),
    description: str = Form(""),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    album = _get_album_or_404(db, album_id)
    album.title = title.strip() or album.title
    album.description = description
    db.commit()
    return RedirectResponse(f"/admin/albums/{album.id}", status_code=303)


@router.post("/{album_id}/delete")
def delete_album(
    album_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    album = _get_album_or_404(db, album_id)
    db.delete(album)
    db.commit()
    shutil.rmtree(storage.album_dir(album_id), ignore_errors=True)
    return RedirectResponse("/admin/albums", status_code=303)


@router.post("/{album_id}/upload")
async def upload_photos(
    album_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    files: list[UploadFile] = File(default=[]),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    album = _get_album_or_404(db, album_id)
    next_order = (
        db.scalar(select(func.max(Photo.sort_order)).where(Photo.album_id == album_id))
        or 0
    )
    added = 0
    for upload in files:
        data = await upload.read()
        if not data or len(data) > settings.max_upload_bytes:
            continue
        try:
            processed = images.process_photo(data, album.id)
        except images.InvalidImageError:
            continue
        next_order += 1
        photo = Photo(
            album_id=album.id,
            filename=processed.filename,
            original_name=upload.filename or "",
            width=processed.width,
            height=processed.height,
            taken_at=processed.taken_at,
            sort_order=next_order,
        )
        db.add(photo)
        db.flush()
        if album.cover_photo_id is None:
            album.cover_photo_id = photo.id
        added += 1
    db.commit()
    return RedirectResponse(f"/admin/albums/{album.id}?uploaded={added}", status_code=303)


@router.post("/reorder")
def reorder_albums(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    order: str = Form(...),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    ids = [int(part) for part in order.split(",") if part.strip().isdigit()]
    for position, album_id in enumerate(ids):
        album = db.get(Album, album_id)
        if album is not None:
            album.sort_order = position
    db.commit()
    return JSONResponse({"ok": True})
