"""Flow tests: can a person actually get where they need to go?

These cover the paths that exist as routes but were unreachable or broken in
the browser: an admin had no link to the create form or the description
editors, and the three edit forms submitted as full page POSTs while their
routes returned a bare fragment, which replaced the whole page with a
`<div class="card-body">` and no header or nav.
"""

import pytest

D1 = "ELIZ-1"
ADMIN = "Kevin"


# --- the edit forms must not blow away the page --------------------------


@pytest.mark.parametrize(
    "path,form",
    [
        (f"/initiatives/{D1}/edit/details", {"name": "Renamed", "description": "d"}),
        (f"/initiatives/{D1}/edit/tags", {"goal": "3", "goal_primary": "3"}),
        (f"/initiatives/{D1}/edit/links", {}),
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
        (f"/initiatives/{D1}/edit/details", {"name": "Renamed", "description": "d"}),
        (f"/initiatives/{D1}/edit/tags", {"goal": "3", "goal_primary": "3"}),
        (f"/initiatives/{D1}/edit/links", {}),
    ],
)
def test_edit_without_javascript_lands_on_a_real_page(logged_in, path, form):
    """The regression: a plain browser submit used to be answered with a bare
    fragment, leaving the user with no header, nav, or way back."""
    client = logged_in(ADMIN)
    response = client.post(path, data=form, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/initiatives/{D1}"

    page = client.get(f"/initiatives/{D1}")
    assert "<html" in page.text
    assert "site-header" in page.text
    assert "site-nav" in page.text


def test_the_edit_forms_actually_submit_over_htmx(logged_in):
    """Belt and braces: assert the markup, so a stray method="post" cannot
    come back unnoticed."""
    body = logged_in(ADMIN).get(f"/initiatives/{D1}/edit/details").text
    assert 'hx-post="/initiatives/ELIZ-1/edit/details"' in body
    assert 'method="post"' not in body


# --- admin entry points must be reachable, not just addressable ------------


def test_admin_sees_a_link_to_the_create_form(logged_in):
    # The admin create link moved into the user menu (blueprint-redesign 5.1);
    # the primary nav no longer carries admin actions.
    assert 'href="/initiatives/new"' in logged_in(ADMIN).get("/").text


def test_non_admin_does_not_see_the_create_link(logged_in):
    assert 'href="/initiatives/new"' not in logged_in("Elizabeth").get("/").text


def test_the_create_link_lands_on_the_form(logged_in):
    response = logged_in(ADMIN).get("/initiatives/new")
    assert response.status_code == 200
    assert 'name="code"' in response.text


def test_goal_list_offers_the_description_editor_to_an_admin(logged_in):
    body = logged_in(ADMIN).get("/goals/3").text
    assert 'href="/entries/goal/3/edit"' in body


def test_priority_list_offers_the_description_editor(logged_in):
    body = logged_in(ADMIN).get("/priorities/Data").text
    assert 'href="/entries/priority/Data/edit"' in body


def test_non_admin_does_not_see_the_description_editor(logged_in):
    assert "/entries/goal/3/edit" not in logged_in("Elizabeth").get("/goals/3").text


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
    """tabindex/role without a key handler is an accessibility promise the app
    does not keep; htmx's hx-trigger supplies Enter and Space natively."""
    body = logged_in("Bill").get("/goals/3").text
    assert 'hx-trigger="click, keyup[key==&#39;Enter&#39;]' in body or \
           "keyup[key=='Enter']" in body
    assert 'tabindex="0"' in body
    assert 'role="link"' in body


def test_person_and_meeting_rows_are_keyboard_reachable(logged_in):
    assert "keyup[key=='Enter']" in logged_in("Bill").get("/people/2").text
    assert "keyup[key=='Enter']" in logged_in("Bill").get("/meeting").text