"""First-run seeding: creates the admin account and default site settings."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import User
from ..security import hash_password
from . import site

settings = get_settings()


def initialize(db: Session) -> None:
    ensure_admin(db)
    site.ensure_defaults(db)


def ensure_admin(db: Session) -> None:
    existing = db.scalar(select(User).where(User.username == settings.admin_username))
    if existing is None:
        db.add(
            User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
            )
        )
        db.commit()
