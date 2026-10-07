"""Flow tests: can a person actually get where they need to go?

These cover the paths that exist as routes but were unreachable or broken in
the browser: an admin had no link to the create form or the description
editors, and the three edit forms submitted as full page POSTs while their
routes returned a bare fragment, which replaced the whole page with a
`<div class="card-body">` and no header or nav.
"""

import pytest

D1 = "MI-004"
ADMIN = "Kevin"


# --- the edit forms must not blow away the page --------------------------


@pytest.mark.parametrize(
    "path,form",
    [
        (f"/major-initiatives/{D1}/edit/details", {"name": "Renamed", "description": "d"}),
        (f"/major-initiatives/{D1}/edit/tags", {"goal": "3", "goal_primary": "3"}),
        (f"/major-initiatives/{D1}/edit/links", {}),
    ],
)
def test_edit_over_htmx_swaps_the_card_in_place(logged_in, path, form):
    client = logged_in(ADMIN)
    response = client.post(path, data=form, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text, "an HTMX edit should return a fragment"
    assert "card-body" in response.text


@pytest.mark.parametrize(
    "path,form",
    [
        (f"/major-initiatives/{D1}/edit/details", {"name": "Renamed", "description": "d"}),
        (f"/major-initiatives/{D1}/edit/tags", {"goal": "3", "goal_primary": "3"}),
        (f"/major-initiatives/{D1}/edit/links", {}),
    ],
)
def test_edit_without_javascript_lands_on_a_real_page(logged_in, path, form):
    """The regression: a plain browser submit used to be answered with a bare
    fragment, leaving the user with no header, nav, or way back."""
    client = logged_in(ADMIN)
    response = client.post(path, data=form, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/major-initiatives/{D1}"

    page = client.get(f"/major-initiatives/{D1}")
    assert "<html" in page.text
    assert "site-header" in page.text
    assert "site-nav" in page.text


def test_the_edit_forms_actually_submit_over_htmx(logged_in):
    """Belt and braces: assert the markup, so a stray method="post" cannot
    come back unnoticed."""
    body = logged_in(ADMIN).get(f"/major-initiatives/{D1}/edit/details").text
    assert 'hx-post="/major-initiatives/MI-004/edit/details"' in body
    assert 'method="post"' not in body


# --- admin entry points must be reachable, not just addressable ------------


def test_admin_sees_a_link_to_the_create_form(logged_in):
    # The admin create link moved into the user menu (blueprint-redesign 5.1);
    # the primary nav no longer carries admin actions.
    assert 'href="/major-initiatives/new"' in logged_in(ADMIN).get("/").text


def test_non_admin_does_not_see_the_create_link(logged_in):
    assert 'href="/major-initiatives/new"' not in logged_in("Elizabeth Smith").get("/").text


def test_the_create_link_lands_on_the_form(logged_in):
    response = logged_in(ADMIN).get("/major-initiatives/new")
    assert response.status_code == 200
    assert 'name="code"' in response.text


def test_goal_list_offers_the_description_editor_to_an_admin(logged_in):
    body = logged_in(ADMIN).get("/goals/3").text
    assert 'href="/entries/goal/3/edit"' in body


def test_priority_list_offers_the_description_editor(logged_in):
    body = logged_in(ADMIN).get("/priorities/Data").text
    assert 'href="/entries/priority/Data/edit"' in body


def test_non_admin_does_not_see_the_description_editor(logged_in):
    assert "/entries/goal/3/edit" not in logged_in("Elizabeth Smith").get("/goals/3").text


def test_editing_a_description_returns_to_the_list(logged_in):
    """Not to the home screen: you edited one goal, you should be back on it."""
    client = logged_in(ADMIN)
    response = client.post("/entries/goal/3/edit", data={"description": "New wording."},
                           follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/goals/3"

    priority = client.post("/entries/priority/Data/edit", data={"description": "New."},
                           follow_redirects=False)
    assert priority.headers["location"] == "/priorities/Data"


# --- keyboard reachability -------------------------------------------------


def test_list_rows_can_be_opened_from_the_keyboard(logged_in):
    """A row opens via a real <a>, which is keyboard-native (Enter, and Space by
    default) and works with JavaScript off.

    Replaced the role="link" + tabindex + hx-trigger pattern (frontend review,
    2026-10-07): role="link" on the <li> removed its listitem role, so the <ul>
    stopped being a list to assistive tech. The anchor also carries hx-get, so
    the drawer still opens in place.
    """
    body = logged_in("Bill Gaudelli").get("/goals/3").text
    assert 'class="row-open"' in body
    assert 'hx-get="/major-initiatives/' in body
    assert 'role="link"' not in body, "the row is an <a> now, not a div-with-role"


def test_person_and_initiative_rows_are_keyboard_reachable(logged_in):
    """The person card's rows open via a real <a> now (frontend review,
    2026-10-07): role="link" + hx-trigger was replaced by an anchor, which is
    keyboard-native and works without JavaScript. The meeting is iced
    (2026-10-06)."""
    body = logged_in("Bill Gaudelli").get("/people/2").text
    assert 'class="row-open"' in body
    assert 'role="link"' not in body