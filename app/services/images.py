"""Image validation, storage, and thumbnail generation (Pillow).

Stored filenames are always server-generated from a random token plus an
extension derived from the *detected* format — never from the user-supplied
filename — so uploads cannot influence the filesystem path.
"""
from __future__ import annotations

import io
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import ALLOWED_IMAGE_FORMATS, get_settings
from . import storage

settings = get_settings()

_EXIF_DATETIME_ORIGINAL = 36867
_EXIF_DATETIME = 306


class InvalidImageError(ValueError):
    """Raised when an upload is not a supported, readable image."""


@dataclass(frozen=True)
class ProcessedPhoto:
    filename: str
    width: int
    height: int
    taken_at: datetime | None


def _open_validated(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Unsupported or corrupt image file.") from exc
    fmt = (img.format or "").upper()
    if fmt not in ALLOWED_IMAGE_FORMATS:
        raise InvalidImageError(f"Unsupported image format: {fmt or 'unknown'}.")
    return img


def _make_filename(fmt: str) -> str:
    return f"{secrets.token_hex(8)}{ALLOWED_IMAGE_FORMATS[fmt]}"


def _exif_taken_at(img: Image.Image) -> datetime | None:
    try:
        exif = img.getexif()
    except Exception:
        return None
    raw = exif.get(_EXIF_DATETIME_ORIGINAL) or exif.get(_EXIF_DATETIME)
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def _write_thumbnail(img: Image.Image, thumb_path: Path) -> None:
    thumb = ImageOps.exif_transpose(img)
    thumb.thumbnail((settings.thumbnail_max_px, settings.thumbnail_max_px))
    save_kwargs: dict[str, object] = {}
    if thumb_path.suffix.lower() in (".jpg", ".jpeg"):
        if thumb.mode not in ("RGB", "L"):
            thumb = thumb.convert("RGB")
        save_kwargs = {"quality": 85, "optimize": True}
    thumb.save(thumb_path, **save_kwargs)


def process_photo(data: bytes, album_id: int) -> ProcessedPhoto:
    """Validate ``data``, persist the original + a thumbnail, return metadata."""
    img = _open_validated(data)
    fmt = (img.format or "").upper()
    filename = _make_filename(fmt)
    original_path = storage.photo_path(album_id, filename)
    original_path.write_bytes(data)
    _write_thumbnail(img, storage.thumb_path(album_id, filename))
    width, height = img.size
    return ProcessedPhoto(filename, width, height, _exif_taken_at(img))


def process_blog_image(data: bytes) -> str:
    """Validate and store a blog cover image; return its stored filename."""
    img = _open_validated(data)
    fmt = (img.format or "").upper()
    filename = _make_filename(fmt)
    (storage.blog_dir() / filename).write_bytes(data)
    return filename
