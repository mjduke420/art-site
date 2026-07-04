"""Hidden admin authentication: login and logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import login_user, logout_user, verify_csrf, verify_password
from ..templating import templates

router = APIRouter()


@router.get("/admin/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": None}
    )


@router.post("/admin/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    if not verify_csrf(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=401,
        )
    login_user(request, user)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    if not verify_csrf(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    logout_user(request)
    return RedirectResponse("/", status_code=303)
