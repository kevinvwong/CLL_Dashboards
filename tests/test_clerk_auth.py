"""The Clerk adapter behind the authenticate() seam (ADR-0004).

Clerk verifies a session token and maps the Clerk user id to a People row. These
tests pin the seam: the provider switch, the safe defaults (no token, bad token,
unlinked user), the id->person mapping, and that the local provider is unchanged.
They do NOT call Clerk's servers; the token verification is exercised with the
SDK's behaviour around a missing/garbage token.
"""
import sqlite3

import pytest

from app import auth, clerk_auth


def _clerk_env(monkeypatch, key="pk_test_ZXhhbXBsZS5jbGVyay5hY2NvdW50cy5kZXYk"):
    monkeypatch.setenv("AUTH_PROVIDER", "clerk")
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_notarealkey")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", key)


def test_the_provider_defaults_to_local(monkeypatch, tmp_path):
    # The DEFAULT, with no .env in play and nothing in the environment, is local.
    # (Config re-reads .env on each call with override=False, so a developer's
    # .env would refill a merely-deleted key; point it at a missing file.)
    from app.config import Config
    monkeypatch.delenv("AUTH_PROVIDER", raising=False)
    cfg = Config(env_path=str(tmp_path / "does-not-exist.env"))
    assert cfg.AUTH_PROVIDER == "local"


def test_no_token_redirects_to_the_clerk_sign_in(monkeypatch, fresh_db):
    _clerk_env(monkeypatch)
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/clerk/sign-in"


def test_a_garbage_token_does_not_authenticate(monkeypatch, fresh_db):
    """A forged/expired token must not become a Principal, and must not 500."""
    _clerk_env(monkeypatch)
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/", headers={"cookie": "__session=not.a.real.token"},
              follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/clerk/sign-in"


def test_the_sign_in_page_renders_with_the_publishable_key(monkeypatch, fresh_db):
    _clerk_env(monkeypatch)
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    body = c.get("/clerk/sign-in").text
    assert "clerk.browser.js" in body
    assert "pk_test_" in body
    # The secret key never reaches the page.
    assert "sk_test_" not in body


def test_the_frontend_api_is_derived_from_the_publishable_key(monkeypatch):
    _clerk_env(monkeypatch)
    assert clerk_auth.frontend_api() == "example.clerk.accounts.dev"
    # A missing/odd key yields empty, not a crash.
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "nonsense")
    assert clerk_auth.frontend_api() == ""


def test_a_person_can_be_linked_to_a_clerk_user(fresh_db):
    auth.link_person_to_clerk(2, "user_abc123")
    person = auth.person_by_clerk_id("user_abc123")
    assert person is not None and person["Name"] == "Elizabeth Smith"
    assert auth.person_by_clerk_id("user_nope") is None
    assert auth.person_by_clerk_id(None) is None


def test_clerk_user_id_is_unique(fresh_db):
    auth.link_person_to_clerk(2, "user_abc123")
    with pytest.raises(sqlite3.IntegrityError):
        auth.link_person_to_clerk(3, "user_abc123")


def test_sign_out_clears_the_session_cookie(monkeypatch, fresh_db):
    _clerk_env(monkeypatch)
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/clerk/sign-out", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/clerk/sign-in"


def test_the_layout_offers_sign_out_under_clerk(monkeypatch, fresh_db):
    _clerk_env(monkeypatch)
    # Sign in as a linked person via a stubbed clerk_user_id, then read the page.
    auth.link_person_to_clerk(1, "user_bill")
    import app.clerk_auth as ca
    monkeypatch.setattr(ca, "clerk_user_id", lambda request: "user_bill")
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    body = c.get("/").text
    assert "/clerk/sign-out" in body
    assert "/whoami" not in body or "Switch user" not in body


def test_the_local_provider_is_unchanged(monkeypatch, fresh_db):
    monkeypatch.setenv("AUTH_PROVIDER", "local")
    from fastapi.testclient import TestClient
    from app.main import app
    from tests.conftest import TEST_PASSCODE
    c = TestClient(app)
    assert c.get("/", follow_redirects=False).headers["location"] == "/login"
    c.post("/login", data={"passcode": TEST_PASSCODE})
    c.post("/whoami", data={"person_id": "1"})
    body = c.get("/").text
    assert "Switch user" in body
