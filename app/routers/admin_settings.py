"""Admin: editable site settings (title, tagline, about, contact) and password change."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import assert_csrf, hash_password, require_admin, verify_password
from ..services import site
from ..templating import templates

router = APIRouter(prefix="/admin/settings")

MIN_PASSWORD_LENGTH = 8


@router.get("")
def settings_form(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "values": site.get_site_settings(db)},
    )


@router.post("")
def update_settings(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    site_title: str = Form(...),
    tagline: str = Form(""),
    about: str = Form(""),
    contact_email: str = Form(""),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    site.set_site_setting(db, "site_title", site_title.strip() or "Portfolio")
    site.set_site_setting(db, "tagline", tagline)
    site.set_site_setting(db, "about", about)
    site.set_site_setting(db, "contact_email", contact_email)
    return RedirectResponse("/admin/settings", status_code=303)


@router.post("/password")
def update_password(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)

    password_error: str | None = None
    if not verify_password(current_password, user.password_hash):
        password_error = "Current password is incorrect."
    elif len(new_password) < MIN_PASSWORD_LENGTH:
        password_error = f"New password must be at least {MIN_PASSWORD_LENGTH} characters."
    elif new_password != confirm_password:
        password_error = "New password and confirmation do not match."

    if password_error:
        return templates.TemplateResponse(
            "admin/settings.html",
            {"request": request, "values": site.get_site_settings(db), "password_error": password_error},
            status_code=400,
        )

    user.password_hash = hash_password(new_password)
    db.commit()
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "values": site.get_site_settings(db),
            "password_success": "Password updated.",
        },
    )
