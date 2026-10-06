"""Task 2.4 check: the access gate.

Covers the shared-access spec (passcode gate, person selection, health check)
and the permission helpers that the admin-editing and progress-updates specs
depend on for their 403 scenarios.
"""

import pytest

PASSCODE = "testpass"


# --- shared-access: passcode gate -----------------------------------------


def test_no_passcode_cookie_redirects_to_login(anon):
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_page_is_reachable_without_a_passcode(anon):
    response = anon.get("/login")
    assert response.status_code == 200
    assert "passcode" in response.text.lower()


def test_wrong_passcode_is_refused_and_sets_no_cookie(anon):
    response = anon.post("/login", data={"passcode": "nope"}, follow_redirects=False)
    assert response.status_code == 401
    assert "cll_passcode" not in response.cookies


def test_correct_passcode_sends_the_user_to_the_person_picker(anon):
    response = anon.post("/login", data={"passcode": PASSCODE}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/whoami"
    assert response.cookies.get("cll_passcode")


# --- shared-access: required person selection -----------------------------


def test_passcode_without_person_redirects_to_picker(anon):
    anon.post("/login", data={"passcode": PASSCODE}, follow_redirects=False)
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/whoami"


def test_picker_lists_active_people(anon):
    anon.post("/login", data={"passcode": PASSCODE}, follow_redirects=False)
    response = anon.get("/whoami")
    assert response.status_code == 200
    for name in ("Bill", "Elizabeth", "Tim", "Mario", "Kevin"):
        assert name in response.text


def test_successful_entry_reaches_the_app_and_shows_the_person(logged_in):
    client = logged_in("Elizabeth")
    response = client.get("/")
    assert response.status_code == 200
    assert "Elizabeth" in response.text
    assert "Switch" in response.text


def test_person_picker_rejects_an_unknown_person(anon):
    anon.post("/login", data={"passcode": PASSCODE}, follow_redirects=False)
    response = anon.post("/whoami", data={"person_id": "9999"}, follow_redirects=False)
    assert response.status_code == 400


def test_tampered_person_cookie_is_ignored(anon):
    anon.post("/login", data={"passcode": PASSCODE}, follow_redirects=False)
    anon.cookies.set("cll_person", "not-a-real-signature")
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/whoami"


# --- shared-access: health check outside the gate -------------------------


def test_healthz_is_outside_the_passcode_gate(anon):
    response = anon.get("/healthz")
    assert response.status_code == 200
    assert response.text.strip() == "ok"


def test_healthz_returns_no_initiative_data(anon):
    body = anon.get("/healthz").text
    for leak in ("ELIZ-", "D-A", "Elizabeth", "Initiative"):
        assert leak not in body


# --- static files are exempt ----------------------------------------------


def test_static_files_are_exempt_from_the_gate(anon):
    response = anon.get("/static/htmx.min.js")
    assert response.status_code == 200
    assert "htmx" in response.text[:2000].lower() or len(response.text) > 1000


# --- design.md decision 5: who counts as the Dean -------------------------


def test_dean_is_bill(logged_in, request_for):
    from app.auth import current_person, is_dean

    person = current_person(request_for(logged_in("Bill")))
    assert person is not None
    assert person["Name"] == "Bill"
    assert is_dean(person) is True


def test_top_level_admin_is_not_the_dean(logged_in, request_for):
    """Kevin also has ReportsToID IS NULL, so that test alone would make him
    the Dean. The 'owns Dean initiatives' clause is what separates them."""
    from app.auth import current_person, is_admin, is_dean

    person = current_person(request_for(logged_in("Kevin")))
    assert person is not None
    assert person["ReportsToID"] is None
    assert is_admin(person) is True
    assert is_dean(person) is False


def test_reports_to_someone_is_not_the_dean(logged_in, request_for):
    from app.auth import current_person, is_dean

    person = current_person(request_for(logged_in("Elizabeth")))
    assert person is not None
    assert person["ReportsToID"] == 1
    assert is_dean(person) is False


# --- can_update / can_edit_details ---------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Elizabeth", True),   # owns ELIZ-1
        ("Tim", False),        # does not own ELIZ-1
        ("Bill", True),        # Dean
        ("Kevin", True),       # admin
    ],
)
def test_can_update_for_a_d1_initiative(logged_in, request_for, name, expected):
    from app.auth import can_update

    request = request_for(logged_in(name))
    assert can_update(request, "ELIZ-1") is expected


def test_non_owner_cannot_edit_details(logged_in, request_for):
    from app.auth import can_edit_details

    assert can_edit_details(request_for(logged_in("Elizabeth")), "ELIZ-1") is True
    assert can_edit_details(request_for(logged_in("Tim")), "ELIZ-1") is False
    # admin may edit details even without ownership
    assert can_edit_details(request_for(logged_in("Kevin")), "ELIZ-1") is True


def test_unknown_initiative_grants_nothing(logged_in, request_for):
    from app.auth import can_edit_details, can_update

    request = request_for(logged_in("Elizabeth"))
    assert can_update(request, "NOPE-9") is False
    assert can_edit_details(request, "NOPE-9") is False


def test_no_person_grants_nothing(anon, request_for):
    from app.auth import can_edit_details, can_update, current_person

    request = request_for(anon)
    assert current_person(request) is None
    assert can_update(request, "ELIZ-1") is False
    assert can_edit_details(request, "ELIZ-1") is False