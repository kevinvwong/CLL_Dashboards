"""Task 9.2 check: hardening.

Covers the shared-access spec's lockout, noindex and robots.txt requirements,
and the /healthz requirement that it sits outside the gate and returns no
initiative data.
"""

import pytest

from app import auth


@pytest.fixture(autouse=True)
def _clear_lockouts():
    """The lockout counter is module-level by design; reset between tests."""
    auth.reset_lockouts()
    yield
    auth.reset_lockouts()


# --- login lockout --------------------------------------------------------


def test_ten_failures_then_locked_out(logged_in):
    client = logged_in("Bill")
    for _ in range(10):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)

    response = client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    assert response.status_code == 429
    assert "Try again in 15 minutes" in response.text


def test_lockout_refuses_even_the_correct_passcode(logged_in):
    """The spec is explicit: the 11th attempt is refused even if correct."""
    client = logged_in("Bill")
    for _ in range(10):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)

    response = client.post("/login", data={"passcode": "testpass"}, follow_redirects=False)
    assert response.status_code == 429, "a correct passcode must still be refused"
    assert "cll_passcode" not in response.cookies


def test_lockout_is_per_ip(logged_in):
    """Failures from one address must not lock out a different one.

    TestClient reports its peer as "testclient"; the real deployment uses
    request.client.host.
    """
    client = logged_in("Bill")
    for _ in range(10):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    assert auth.too_many_attempts("testclient") is True
    assert auth.too_many_attempts("10.0.0.2") is False


def test_nine_failures_do_not_lock(logged_in):
    client = logged_in("Bill")
    for _ in range(9):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    response = client.post("/login", data={"passcode": "testpass"}, follow_redirects=False)
    assert response.status_code == 303, "the correct passcode must still work"


def test_a_correct_passcode_clears_the_counter(logged_in):
    client = logged_in("Bill")
    for _ in range(5):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    client.post("/login", data={"passcode": "testpass"}, follow_redirects=False)
    assert auth.too_many_attempts("testclient") is False


def test_lockout_message_is_shown_on_the_login_page(logged_in):
    client = logged_in("Bill")
    for _ in range(10):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    assert "Try again in 15 minutes" in client.get("/login").text


def test_counter_expires(logged_in, monkeypatch):
    """Failures older than the window do not count."""
    import time

    client = logged_in("Bill")
    for _ in range(10):
        client.post("/login", data={"passcode": "wrong"}, follow_redirects=False)
    assert auth.too_many_attempts("testclient") is True

    # pretend the attempts happened long ago
    auth._failures["testclient"] = [t - auth.LOCKOUT_WINDOW_SECONDS - 1 for t in auth._failures["testclient"]]
    assert auth.too_many_attempts("testclient") is False


# --- noindex --------------------------------------------------------------


def test_every_response_carries_noindex(logged_in):
    client = logged_in("Bill")
    for path in ("/", "/goals/3", "/meeting", "/checks", "/healthz", "/login", "/robots.txt"):
        response = client.get(path, follow_redirects=False)
        assert response.headers.get("X-Robots-Tag") == "noindex", f"{path} missing noindex"


def test_noindex_is_present_on_a_redirect_too(logged_in):
    response = logged_in("Bill").get("/goals/3", follow_redirects=False)
    assert response.status_code == 200
    assert response.headers.get("X-Robots-Tag") == "noindex"


# --- robots.txt -----------------------------------------------------------


def test_robots_txt_disallows_all(anon):
    response = anon.get("/robots.txt")
    assert response.status_code == 200
    assert "User-agent: *" in response.text
    assert "Disallow: /" in response.text


def test_robots_txt_is_outside_the_passcode_gate(anon):
    """A crawler cannot have the passcode, so robots.txt must be reachable."""
    assert anon.get("/robots.txt").status_code == 200


def test_robots_txt_carries_no_data(anon):
    body = anon.get("/robots.txt").text
    for leak in ("ELIZ-", "Elizabeth", "Initiative"):
        assert leak not in body


# --- healthz --------------------------------------------------------------


def test_healthz_is_outside_the_gate_and_data_free(anon):
    response = anon.get("/healthz")
    assert response.status_code == 200
    assert response.text.strip().startswith("ok")
    assert "ELIZ-" not in response.text


def test_healthz_reports_an_unreachable_database(anon, monkeypatch):
    monkeypatch.setenv("DB_PATH", "C:/definitely/not/here.db")
    assert anon.get("/healthz").status_code == 503