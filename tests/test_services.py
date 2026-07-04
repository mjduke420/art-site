"""Unit tests for the service layer (text, images)."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.database import SessionLocal
from app.models import Album
from app.services import images, storage, text


def _jpeg_bytes(size=(120, 80)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (100, 150, 200)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_slugify_basic():
    assert text.slugify("Hello, World!") == "hello-world"
    assert text.slugify("  Multiple   Spaces ") == "multiple-spaces"
    assert text.slugify("***") == "item"


def test_render_markdown_strips_scripts():
    rendered = text.render_markdown("**bold** <script>alert(1)</script>")
    assert "<strong>bold</strong>" in rendered
    assert "<script>" not in rendered


def test_process_photo_writes_files():
    processed = images.process_photo(_jpeg_bytes(), album_id=99999)
    assert (processed.width, processed.height) == (120, 80)
    assert storage.photo_path(99999, processed.filename).exists()
    assert storage.thumb_path(99999, processed.filename).exists()


def test_process_photo_rejects_non_image():
    with pytest.raises(images.InvalidImageError):
        images.process_photo(b"this is not an image", album_id=1)


def test_unique_slug_increments():
    db = SessionLocal()
    try:
        first = text.unique_slug(db, Album, "Sunset")
        db.add(Album(title="Sunset", slug=first, sort_order=0))
        db.commit()
        second = text.unique_slug(db, Album, "Sunset")
        assert first == "sunset"
        assert second == "sunset-2"
    finally:
        db.close()
