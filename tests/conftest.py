"""Test fixtures. Configures an isolated data dir for each test run."""
from __future__ import annotations

import os
import tempfile

import pytest

# Configure environment BEFORE importing the app (settings are cached).
_TMP_DATA = tempfile.mkdtemp(prefix="portfolio-test-")
os.environ["DATA_DIR"] = _TMP_DATA
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-pass"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(client):
    import re

    html = client.get("/admin/login").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "test-pass", "csrf_token": token},
        follow_redirects=False,
    )
    return client
