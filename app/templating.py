"""Shared Jinja2 templating setup and helper globals/filters."""
from __future__ import annotations

from markupsafe import Markup

from fastapi.templating import Jinja2Templates

from .config import get_settings
from .security import ensure_csrf_token
from .services import storage, text

settings = get_settings()

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["default_site_title"] = settings.site_title
templates.env.globals["image_url"] = storage.image_url
templates.env.globals["thumb_url"] = storage.thumb_url
templates.env.globals["blog_image_url"] = storage.blog_image_url
templates.env.globals["csrf_token"] = ensure_csrf_token
templates.env.filters["markdown"] = lambda value: Markup(text.render_markdown(value or ""))


def _human_date(value, style: str = "long") -> str:
    """Portable date formatting (avoids the Linux-only ``%-d`` strftime flag)."""
    if value is None:
        return ""
    month = value.strftime("%B" if style == "long" else "%b")
    return f"{month} {value.day}, {value.year}"


templates.env.filters["humandate"] = _human_date
