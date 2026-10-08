"""Test fixtures for the initiative dashboard.

Each test gets its own copy of the sample database so writes never leak
between cases. `logged_in` returns a TestClient already carrying both the
passcode cookie and a chosen person cookie, which is what the specs call a
"signed-in person".
"""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

# The repo root is one level up from tests/. pyproject.toml sets
# pythonpath = ["."], so `import app` resolves without a sys.path hack.
REPO = Path(__file__).resolve().parents[1]
REPO_DB = REPO / "cll_initiatives.db"

from app.main import app  # noqa: E402  (path comes from pyproject's pythonpath)

TEST_PASSCODE = "testpass"


def person_id(db_path: Path, name: str):
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT PersonID FROM People WHERE Name = ?", (name,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


# Register rows the tests use, with the role each retired sample code had:
#   MI-002 'Reusable content'      owned by Mario Herane  (was D-A / a Dean row)
#   MI-004 'Team operating models' owned by Elizabeth Smith (was ELIZ-1)
#   MI-001 'Portfolio & pathways'  owned by Tim Jacobbe (was TIM-*)
# The tests reference these by MI-id; this keeps the mapping in one place.
MI_BY_MARIO = "MI-002"
MI_BY_ELIZABETH = "MI-004"
MI_BY_TIM = "MI-001"
NO_SUCH_MI = "MI-999"


def add_update(db_path, mi_id: str, percent: int, status: str,
               note: str = "", on: str = "2026-10-05", by: int = 5):
    """Append one diary entry to a Team Initiative, for tests that need one.

    The register seed ships no diary (the prototype's sample diary was dropped
    in the merge), so any test that asserts on progress, staleness or the
    meeting must seed its own entry. Writing directly, like the rest of the
    fixtures, so the test does not depend on repo's validation.
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO TeamInitiativeUpdates "
            "(TeamInitiativeID, UpdateDate, PercentComplete, Status, Note, EnteredByID, CreatedAt) "
            "SELECT TeamInitiativeID, ?, ?, ?, ?, ?, ? || ' 08:00:00' "
            "FROM TeamInitiatives WHERE MIId = ?",
            (on, percent, status, note or None, by, on, mi_id),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """A private copy of the sample database, pointed at by DB_PATH."""
    db = tmp_path / "cll_initiatives.db"
    shutil.copy2(REPO_DB, db)
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("APP_PASSCODE", TEST_PASSCODE)
    monkeypatch.setenv("APP_SECRET", "testsecret")
    monkeypatch.setenv("APP_ENV", "test")
    # Pin the auth provider. A developer's .env may set AUTH_PROVIDER=clerk to
    # run the app locally; without this the whole suite would run under Clerk and
    # the passcode login the fixtures use would not apply. Clerk tests override
    # this explicitly, so the suite is deterministic either way.
    monkeypatch.setenv("AUTH_PROVIDER", "local")
    monkeypatch.delenv("CLERK_SECRET_KEY", raising=False)
    monkeypatch.delenv("CLERK_PUBLISHABLE_KEY", raising=False)
    return db


@pytest.fixture
def diary(fresh_db):
    """Seed a Team Initiative diary entry into this test's database.

    Usage: diary("MI-004", 25, "On track", on="2026-09-20")
    """
    def _add(mi_id, percent, status, note="", on="2026-10-05", by=5):
        add_update(fresh_db, mi_id, percent, status, note=note, on=on, by=by)

    return _add


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
    """Return a factory: logged_in("Bill Gaudelli") -> TestClient signed in as Bill Gaudelli."""

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