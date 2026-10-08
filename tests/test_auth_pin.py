"""The auth stopgap: a PIN closes the self-asserted person picker.

The escalation vector was never the passcode - it was that POST /whoami let
anyone holding the passcode become any person, including the admin. A PIN that
only that person knows closes it. This pins the seam (ADR-0004) and the local
roles (ADR-0005).
"""
import sqlite3

from app import auth
from tests.conftest import TEST_PASSCODE


def _set_pin(db, name, pin):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE People SET Credential = ? WHERE Name = ?",
                 (auth.hash_pin(pin), name))
    conn.commit()
    conn.close()


def test_hash_and_check_round_trip():
    h = auth.hash_pin("4821")
    assert h != "4821" and h.startswith("pbkdf2_sha256$")
    assert auth.check_pin(h, "4821") is True
    assert auth.check_pin(h, "4822") is False
    assert auth.check_pin("garbage", "4821") is False


def test_without_a_pin_the_picker_still_works(anon):
    """Nothing breaks before PINs are provisioned."""
    anon.post("/login", data={"passcode": TEST_PASSCODE})
    r = anon.post("/whoami", data={"person_id": "1"}, follow_redirects=False)
    assert r.status_code == 303


def test_a_pin_is_required_once_set(fresh_db, anon):
    """The core: with a PIN set, the passcode alone cannot become that person."""
    _set_pin(fresh_db, "Bill Gaudelli", "4821")
    anon.post("/login", data={"passcode": TEST_PASSCODE})

    wrong = anon.post("/whoami", data={"person_id": "1", "pin": "0000"},
                      follow_redirects=False)
    assert wrong.status_code == 401, "a wrong PIN was accepted"
    assert "not right" in wrong.text

    right = anon.post("/whoami", data={"person_id": "1", "pin": "4821"},
                      follow_redirects=False)
    assert right.status_code == 303


def test_an_admin_sets_a_pin_but_a_non_admin_cannot(logged_in, fresh_db):
    admin = logged_in("Kevin")
    # Set Elizabeth's PIN (not Bill's, so this test can still log in as Bill below).
    r = admin.post("/people/2/set-pin", data={"pin": "1234"}, follow_redirects=False)
    assert r.status_code == 303
    assert auth.person_credential(2) is not None

    dean = logged_in("Bill Gaudelli")
    r = dean.post("/people/3/set-pin", data={"pin": "1234"})
    assert r.status_code == 403


def test_roles_are_seeded_with_the_canonical_set(fresh_db):
    """The six DR-05 roles, assigned by the person's state (DR-23)."""
    rows = {r[0]: r[1] for r in sqlite3.connect(fresh_db).execute(
        "SELECT p.Name, group_concat(r.Name) FROM PeopleRoles pr "
        "JOIN People p ON p.PersonID=pr.PersonID JOIN Roles r ON r.RoleID=pr.RoleID "
        "GROUP BY p.PersonID")}
    assert "PlatformAdmin" in rows["Kevin"]
    assert "Operator" in rows["Kevin"]
    assert "ExecutiveSponsor" in rows["Bill Gaudelli"]
    assert "DataOwner" in rows["Elizabeth Smith"]


def test_authenticate_returns_a_principal_with_roles(logged_in):
    client = logged_in("Kevin")
    from starlette.requests import Request
    cookie = "; ".join(f"{n}={v}" for n, v in client.cookies.items())
    scope = {"type": "http", "http_version": "1.1", "method": "GET", "path": "/",
             "root_path": "", "scheme": "http", "query_string": b"",
             "headers": [(b"cookie", cookie.encode())], "server": ("t", None),
             "client": ("t", None), "app": None}
    principal = auth.authenticate(Request(scope))
    assert principal is not None
    assert principal.name == "Kevin"
    assert principal.has_role("PlatformAdmin")
