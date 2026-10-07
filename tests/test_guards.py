"""Request guards: existence before permission, enforced once per route.

Covers the `request-guards` spec of deepen-dashboard-modules.

The guards are exercised through the routes that use them, because the route is
where the ordering is observable. A guard that is correct in isolation but wired
in the wrong order is the failure this spec exists to prevent.
"""
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, "app")


def _main_source():
    return open(os.path.join(SRC, "main.py"), encoding="utf-8").read()


# --- existence before permission -------------------------------------------


def test_unknown_code_is_404_even_for_a_caller_who_could_edit(logged_in):
    """The order the spec names: 404 first, regardless of the caller.

    Bill Gaudelli is the Dean and an admin, so on a real code he would be allowed. On an
    unknown code he must still get 404 - not 403, which would leak that the code
    is special and contradict GET /initiatives/{code}.
    """
    client = logged_in("Bill Gaudelli")
    for path in ("/initiatives/NOPE-9",
                 "/initiatives/NOPE-9/update",
                 "/initiatives/NOPE-9/edit/details",
                 "/initiatives/NOPE-9/edit/tags"):
        r = client.get(path)
        assert r.status_code == 404, "%s returned %d, expected 404" % (path, r.status_code)


def test_known_but_forbidden_is_403(logged_in):
    """A code that exists, that this caller may not act on, is forbidden."""
    r = logged_in("Tim Jacobbe").get("/initiatives/ELIZ-1/update")
    assert r.status_code == 403


# --- permission is enforced on the server -----------------------------------


def test_direct_post_without_permission_is_refused(logged_in, fresh_db):
    """Tim Jacobbe does not own ELIZ-1 and is not the Dean; a direct POST is refused."""
    r = logged_in("Tim Jacobbe").post(
        "/initiatives/ELIZ-1/updates",
        data={"percent": "10", "status": "On track", "note": "sneaking in"},
        follow_redirects=False,
    )
    assert r.status_code == 403


def test_admin_only_post_is_refused_for_a_non_admin(logged_in):
    """An owner who is not an admin cannot edit tags, even on their own item."""
    r = logged_in("Elizabeth Smith").post(
        "/initiatives/ELIZ-1/edit/tags",
        data={"goal": ["1"]},
        follow_redirects=False,
    )
    assert r.status_code == 403


# --- the caller is resolved once -------------------------------------------


def test_the_person_is_resolved_once_per_request(logged_in, fresh_db, request_for, monkeypatch):
    """Two asks in one request read the database once.

    Counts the connections the person lookup opens; the cached person means the
    second ask costs nothing. This is the "resolved once per request" rule.
    """
    from app import auth

    # Build the request FIRST: logged_in() runs real requests whose middleware
    # calls current_person, which would pollute the count. The counter starts
    # after the session is established.
    req = request_for(logged_in("Bill Gaudelli"))

    calls = {"n": 0}
    real = auth._conn

    def counting():
        calls["n"] += 1
        return real()

    monkeypatch.setattr(auth, "_conn", counting)

    first = auth.current_person(req)
    after_first = calls["n"]
    second = auth.current_person(req)

    assert first is not None
    assert first["Name"] == "Bill Gaudelli"
    assert second["Name"] == "Bill Gaudelli"
    assert after_first == 1, "the first ask opened %d connections, expected 1" % after_first
    assert calls["n"] == 1, "the second ask hit the database again"


# --- the guard is declared, not repeated -----------------------------------


def test_no_route_still_repeats_the_admin_guard():
    """The admin check lives in the guard, not in each route body.

    A grep for the old per-route clause; if it returns, the chain has been
    re-inlined somewhere.
    """
    text = _main_source()
    offenders = [l.strip() for l in text.splitlines()
                 if "if not auth.is_admin_request(request)" in l]
    assert not offenders, (
        "an admin guard was re-inlined in a route:\n" + "\n".join(offenders)
    )


def test_no_route_still_repeats_the_existence_then_permission_pair():
    """The 404-then-403 pair lives in the guard, not in route bodies."""
    text = _main_source()
    pairs = re.findall(
        r"initiative_card\(code\) is None.*\n.*can_(?:update|edit_details)\(", text)
    assert not pairs, "a route still repeats the 404-then-403 pair"
