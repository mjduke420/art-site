"""Authentication, password hashing, and CSRF protection.

Session state (signed cookie) holds ``user_id`` once logged in and a
per-session ``csrf_token`` used to protect admin form submissions.
"""
from __future__ import annotations

import secrets

import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

# bcrypt only hashes the first 72 bytes of input.
_BCRYPT_MAX_BYTES = 72


class NotAuthenticatedError(Exception):
    """Raised by admin dependencies when no valid session exists."""


def hash_password(password: str) -> str:
    salted = bcrypt.hashpw(password.encode("utf-8")[:_BCRYPT_MAX_BYTES], bcrypt.gensalt())
    return salted.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8")[:_BCRYPT_MAX_BYTES], hashed.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def ensure_csrf_token(request: Request) -> str:
    """Return the session CSRF token, creating one if needed."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, submitted: str | None) -> bool:
    token = request.session.get("csrf_token")
    return bool(token) and bool(submitted) and secrets.compare_digest(token, submitted)


def assert_csrf(request: Request, submitted: str | None) -> None:
    """Raise 403 unless the submitted token matches the session token."""
    if not verify_csrf(request, submitted):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def login_user(request: Request, user: User) -> None:
    request.session["user_id"] = user.id


def logout_user(request: Request) -> None:
    request.session.clear()


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency: returns the logged-in admin or triggers a login redirect."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticatedError()
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise NotAuthenticatedError()
    return user
