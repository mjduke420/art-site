"""Editable site-wide settings stored as key/value rows."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Setting

settings = get_settings()

DEFAULTS: dict[str, str] = {
    "site_title": settings.site_title,
    "tagline": "Photo Portfolio",
    "about": "Welcome to my photo portfolio. Edit this bio from the admin settings page.",
    "contact_email": "",
}

EDITABLE_KEYS = tuple(DEFAULTS.keys())


def get_site_settings(db: Session) -> dict[str, str]:
    values = dict(DEFAULTS)
    for row in db.query(Setting).all():
        values[row.key] = row.value
    return values


def set_site_setting(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row is None:
        db.add(Setting(key=key, value=value))
    else:
        row.value = value
    db.commit()


def ensure_defaults(db: Session) -> None:
    changed = False
    for key, value in DEFAULTS.items():
        if db.get(Setting, key) is None:
            db.add(Setting(key=key, value=value))
            changed = True
    if changed:
        db.commit()
