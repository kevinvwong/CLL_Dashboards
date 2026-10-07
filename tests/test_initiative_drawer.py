"""Group 4 of blueprint-redesign: the initiative drawer.

Covers the drawer/full-page split, the partial-response rule, the detail layout,
the update form, and the inline save. Some of the partial-response work landed
in group 1; these assert it from the drawer's point of view.
"""
import html as _html
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 4.1 the drawer and the full page ---------------------------------------


def test_a_partial_request_carries_no_document_or_nav(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1",
                                 headers={"HX-Request": "true"}).text
    assert "<html" not in body.lower()
    assert "site-nav" not in body


def test_a_direct_load_is_a_full_page_with_no_close_control(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1").text
    assert "<html" in body.lower()
    assert "site-nav" in body
    assert 'class="card-close"' not in body, "a full page showed a close control"


def test_the_drawer_fragment_has_a_close_control(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1",
                                 headers={"HX-Request": "true"}).text
    assert 'class="card-close"' in body


def test_the_drawer_is_a_right_side_dialog_over_the_list(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1",
                                 headers={"HX-Request": "true"}).text
    assert 'role="document"' in body
    # The shell declares itself modal at the base layout level.
    full = logged_in("Bill Gaudelli").get("/").text
    assert 'aria-modal="true"' in full
    assert 'class="card-modal drawer"' in full


# --- 4.2 the partial-response rule on every endpoint ------------------------


@pytest.mark.parametrize("path", [
    "/initiatives/ELIZ-1/edit/details",
    "/initiatives/ELIZ-1/edit/tags",
    "/initiatives/ELIZ-1/edit/links",
    "/initiatives/ELIZ-1/update",
])
def test_every_edit_endpoint_splits_fragment_and_full(logged_in, path):
    frag = logged_in("Kevin").get(path, headers={"HX-Request": "true"}).text
    full = logged_in("Kevin").get(path).text
    assert "<html" not in frag.lower() and "site-nav" not in frag
    assert "<html" in full.lower() and "site-nav" in full


# --- 4.3 the drawer layout ---------------------------------------------------


def test_the_detail_shows_header_status_progress_owner(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1").text)
    assert "detail-header" in body
    assert 'role="progressbar"' in body
    assert 'aria-valuenow=' in body
    assert "Owner:" in body


def test_the_detail_lists_relationships_with_status_and_progress(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1").text)
    assert "card-connections" in body
    # Both a status pill and a percentage appear on the relationship rows.
    assert "connection-status" in body
    assert "%" in body


def test_the_diary_is_newest_first(logged_in):
    from app import queries
    diary = queries.initiative_card("ELIZ-1")["diary"]
    assert diary, "no diary entries"
    dates = [d["UpdateDate"] for d in diary]
    assert dates == sorted(dates, reverse=True), dates


# --- 4.4 the update form -----------------------------------------------------


def test_the_update_form_has_progress_and_status_controls(logged_in):
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1/update",
                                 headers={"HX-Request": "true"}).text
    assert 'name="percent"' in body
    assert 'name="status"' in body
    assert 'name="note"' in body


def test_the_status_control_offers_exactly_the_schema_values(logged_in):
    from app import repo
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1/update",
                                 headers={"HX-Request": "true"}).text
    options = re.findall(r'<option value="([^"]+)"', body)
    assert sorted(options) == sorted(repo.STATUSES)


def test_the_form_shows_the_previous_value(logged_in):
    """The control is set to the initiative's current progress."""
    from app import queries
    card = queries.initiative_card("ELIZ-1")
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1/update",
                                 headers={"HX-Request": "true"}).text
    # The slider value equals the latest percent.
    assert 'value="%s"' % card["latest"]["PercentComplete"] in body


def test_the_note_has_a_character_limit(logged_in):
    from app import repo
    body = logged_in("Bill Gaudelli").get("/initiatives/ELIZ-1/update",
                                 headers={"HX-Request": "true"}).text
    assert ('maxlength="%d"' % repo.NOTE_MAX) in body


# --- 4.5 inline save ---------------------------------------------------------


def test_a_successful_save_returns_the_card_and_triggers_refresh(logged_in):
    r = logged_in("Elizabeth Smith").post(
        "/initiatives/ELIZ-1/updates",
        data={"percent": "50", "status": "On track", "note": "halfway"},
        headers={"HX-Request": "true"}, follow_redirects=False)
    assert r.status_code == 200
    # The response is the card fragment, and it asks the list to refresh.
    assert "<html" not in r.text.lower()
    assert "HX-Trigger" in r.headers or "initiativeUpdated" in r.headers.get("HX-Trigger", "")


def test_a_refused_save_keeps_the_form_and_explains(logged_in):
    r = logged_in("Elizabeth Smith").post(
        "/initiatives/ELIZ-1/updates",
        data={"percent": "150", "status": "On track", "note": "x"},
        headers={"HX-Request": "true"}, follow_redirects=False)
    assert r.status_code == 422
    # The form is returned with the reason, not a bare error.
    assert 'name="percent"' in r.text
    assert "role=\"alert\"" in r.text


def test_the_toast_slot_exists(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'id="toast"' in body
    assert 'aria-live="polite"' in body
