"""Filesystem layout and URL helpers for uploaded images.

Everything lives under ``data/uploads`` which is mounted as a Docker volume:

    uploads/albums/<album_id>/<filename>
    uploads/albums/<album_id>/thumb_<filename>
    uploads/blog/<filename>

Album files are keyed by the album's numeric id (stable across renames).
"""
from __future__ import annotations

from pathlib import Path

from ..config import get_settings

settings = get_settings()


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def album_dir(album_id: int) -> Path:
    return _ensure(settings.uploads_dir / "albums" / str(album_id))


def blog_dir() -> Path:
    return _ensure(settings.uploads_dir / "blog")


def photo_path(album_id: int, filename: str) -> Path:
    return album_dir(album_id) / filename


def thumb_path(album_id: int, filename: str) -> Path:
    return album_dir(album_id) / f"thumb_{filename}"


def delete_photo_files(album_id: int, filename: str) -> None:
    photo_path(album_id, filename).unlink(missing_ok=True)
    thumb_path(album_id, filename).unlink(missing_ok=True)


def delete_blog_image(filename: str | None) -> None:
    if filename:
        (blog_dir() / filename).unlink(missing_ok=True)


def image_url(album_id: int, filename: str) -> str:
    return f"/uploads/albums/{album_id}/{filename}"


def thumb_url(album_id: int, filename: str) -> str:
    return f"/uploads/albums/{album_id}/thumb_{filename}"


def blog_image_url(filename: str | None) -> str | None:
    if not filename:
        return None
    return f"/uploads/blog/{filename}"
