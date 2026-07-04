"""HTTP-level tests for public pages and the admin flow."""
from __future__ import annotations

import re


def _csrf(client, path: str) -> str:
    html = client.get(path).text
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, f"no csrf token found on {path}"
    return match.group(1)


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_home_renders(client):
    response = client.get("/")
    assert response.status_code == 200


def test_blog_index_renders(client):
    assert client.get("/blog").status_code == 200


def test_admin_requires_login(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_login_with_bad_password(client):
    token = _csrf(client, "/admin/login")
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "nope", "csrf_token": token},
    )
    assert response.status_code == 401


def test_login_then_dashboard(admin_client):
    response = admin_client.get("/admin")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_create_album_appears_on_home(admin_client):
    token = _csrf(admin_client, "/admin/albums/new")
    response = admin_client.post(
        "/admin/albums",
        data={"title": "Test Album", "description": "desc", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Test Album" in admin_client.get("/").text


def test_csrf_is_enforced(admin_client):
    response = admin_client.post(
        "/admin/albums",
        data={"title": "No CSRF", "csrf_token": "wrong-token"},
    )
    assert response.status_code == 403


def _jpeg_bytes() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (60, 40), (20, 120, 80)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_blog_post_with_gallery(admin_client):
    token = _csrf(admin_client, "/admin/blog/new")
    files = [("gallery", (f"g{i}.jpg", _jpeg_bytes(), "image/jpeg")) for i in range(3)]
    response = admin_client.post(
        "/admin/blog",
        data={"title": "Trip Post", "body": "A trip.", "published": "1", "csrf_token": token},
        files=files,
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = admin_client.get("/blog/trip-post")
    assert page.status_code == 200
    assert page.text.count("data-lightbox") == 3


def test_blog_gallery_capped_at_max(admin_client):
    token = _csrf(admin_client, "/admin/blog/new")
    files = [("gallery", (f"m{i}.jpg", _jpeg_bytes(), "image/jpeg")) for i in range(13)]
    admin_client.post(
        "/admin/blog",
        data={"title": "Big Series", "body": "x", "published": "1", "csrf_token": token},
        files=files,
        follow_redirects=False,
    )
    page = admin_client.get("/blog/big-series")
    assert page.text.count("data-lightbox") == 10


def test_change_password_wrong_current(admin_client):
    token = _csrf(admin_client, "/admin/settings")
    response = admin_client.post(
        "/admin/settings/password",
        data={
            "current_password": "not-the-password",
            "new_password": "new-strong-pass",
            "confirm_password": "new-strong-pass",
            "csrf_token": token,
        },
    )
    assert response.status_code == 400
    assert "incorrect" in response.text


def test_change_password_mismatch(admin_client):
    token = _csrf(admin_client, "/admin/settings")
    response = admin_client.post(
        "/admin/settings/password",
        data={
            "current_password": "test-pass",
            "new_password": "new-strong-pass",
            "confirm_password": "different-pass",
            "csrf_token": token,
        },
    )
    assert response.status_code == 400
    assert "do not match" in response.text


def test_change_password_success_and_relogin(admin_client):
    token = _csrf(admin_client, "/admin/settings")
    response = admin_client.post(
        "/admin/settings/password",
        data={
            "current_password": "test-pass",
            "new_password": "new-strong-pass",
            "confirm_password": "new-strong-pass",
            "csrf_token": token,
        },
    )
    assert response.status_code == 200
    assert "Password updated" in response.text

    admin_client.post(
        "/admin/logout",
        data={"csrf_token": _csrf(admin_client, "/admin/settings")},
        follow_redirects=False,
    )

    login_token = _csrf(admin_client, "/admin/login")
    old_password_attempt = admin_client.post(
        "/admin/login",
        data={"username": "admin", "password": "test-pass", "csrf_token": login_token},
    )
    assert old_password_attempt.status_code == 401

    login_token = _csrf(admin_client, "/admin/login")
    new_password_attempt = admin_client.post(
        "/admin/login",
        data={"username": "admin", "password": "new-strong-pass", "csrf_token": login_token},
        follow_redirects=False,
    )
    assert new_password_attempt.status_code == 303
