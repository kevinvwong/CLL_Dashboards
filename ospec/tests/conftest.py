"""Test fixtures for the initiative dashboard.

Each test gets its own copy of the sample database so writes never leak
between cases. `logged_in` returns a TestClient already carrying both the
passcode cookie and a chosen person cookie, which is what the specs call a
"signed-in person".
"""

import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

APP_HOME = Path(__file__).resolve().parents[1]
# ospec/ is one level up from tests/: tests -> ospec
REPO_DB = Path(__file__).resolve().parents[1] / "cll_initiatives.db"

sys.path.insert(0, str(APP_HOME))

from app.main import app  # noqa: E402  (needs the path insert above)

TEST_PASSCODE = "testpass"


def person_id(db_path: Path, name: str):
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT PersonID FROM People WHERE Name = ?", (name,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """A private copy of the sample database, pointed at by DB_PATH."""
    db = tmp_path / "cll_initiatives.db"
    shutil.copy2(REPO_DB, db)
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("APP_PASSCODE", TEST_PASSCODE)
    monkeypatch.setenv("APP_SECRET", "testsecret")
    monkeypatch.setenv("APP_ENV", "test")
    return db


@pytest.fixture
def anon(fresh_db):
    """A client with no passcode and no person cookie."""
    return TestClient(app)


@pytest.fixture
def meeting_on(fresh_db, monkeypatch):
    """Enable the iced meeting surface for the cases that verify it is intact.

    The meeting is hidden from the nav and its route 404s by default
    (MEETING_ENABLED unset, 2026-10-06). These tests prove the page, its
    queries and its rendering still work, so re-enabling it is one environment
    variable rather than a rebuild.
    """
    monkeypatch.setenv("MEETING_ENABLED", "1")
    return True


@pytest.fixture
def request_for(fresh_db):
    """Build a Starlette Request carrying a client's cookies.

    `TestClient.build_request` returns an httpx request, which the auth
    helpers (written against Starlette) cannot read. Tests that exercise
    permission helpers directly need this instead of going through a route.
    """

    def _request(client, path: str = "/") -> Request:
        # Starlette reads cookies from a single "cookie" header, so the
        # client's cookie jar has to be joined into one, not sent as
        # repeated headers.
        cookie = "; ".join(f"{name}={value}" for name, value in client.cookies.items())
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "root_path": "",
            "scheme": "http",
            "query_string": b"",
            "headers": [(b"cookie", cookie.encode())] if cookie else [],
            "server": ("testserver", None),
            "client": ("testclient", None),
            "app": app,
        }
        return Request(scope)

    return _request


@pytest.fixture
def logged_in(fresh_db):
    """Return a factory: logged_in("Bill") -> TestClient signed in as Bill."""

    def _login(name: str) -> TestClient:
        client = TestClient(app)
        first = client.post(
            "/login", data={"passcode": TEST_PASSCODE}, follow_redirects=False
        )
        assert first.status_code == 303, first.text
        pid = person_id(fresh_db, name)
        assert pid is not None, f"no person named {name!r} in the sample data"
        second = client.post(
            "/whoami", data={"person_id": pid}, follow_redirects=False
        )
        assert second.status_code == 303, second.text
        return client

    return _login