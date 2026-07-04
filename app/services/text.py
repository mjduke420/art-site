"""Slug generation and safe Markdown rendering."""
from __future__ import annotations

import re

import bleach
import markdown as md
from sqlalchemy import select
from sqlalchemy.orm import Session

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_ALLOWED_TAGS = [
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "b", "i", "u", "s", "a", "ul", "ol", "li",
    "blockquote", "code", "pre", "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "th", "td", "span", "div",
]
_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "loading"],
    "span": ["class"],
    "div": ["class"],
    "code": ["class"],
}


def slugify(value: str) -> str:
    cleaned = _SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return cleaned or "item"


def unique_slug(db: Session, model: type, title: str, *, exclude_id: int | None = None) -> str:
    """Return a slug for ``title`` unique within ``model`` (skipping ``exclude_id``)."""
    base = slugify(title)
    slug = base
    counter = 2
    while True:
        existing = db.scalar(select(model).where(model.slug == slug))
        if existing is None or existing.id == exclude_id:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def render_markdown(value: str) -> str:
    html = md.markdown(
        value or "", extensions=["fenced_code", "tables", "sane_lists", "nl2br"]
    )
    return bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
