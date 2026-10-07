"""Task 6.5 check: progress updates.

Covers the progress-updates spec: append-only history, percent validation,
server-side 403 for a non-owner, the Update button's visibility, and the rule
that a D-1 update never rolls up to a Dean initiative.
"""

import sqlite3

import pytest

D1 = "MI-004"
DEAN = "MI-002"
ELIZABETH = 2
ELIZABETH_NAME = "Elizabeth Smith"


def _diary(fresh_db, code):
    """The card's diary, read through the same read the app renders from.

    This used to re-implement the diary SQL. It now imports it, so a change to
    how the diary is read is exercised here rather than passing against a copy
    (task 6.3).
    """
    from app import queries

    return queries.initiative_card(code)["diary"]


def _count(fresh_db):
    conn = sqlite3.connect(fresh_db)
    n = conn.execute("SELECT COUNT(*) FROM MajorInitiativeUpdates").fetchone()[0]
    conn.close()
    return n


# --- append-only ----------------------------------------------------------


def test_update_is_appended_not_replaced(logged_in, fresh_db):
    before = _diary(fresh_db, D1)
    response = logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                          data={"percent": 55, "status": "At risk", "note": "halfway"})
    assert response.status_code == 200
    after = _diary(fresh_db, D1)
    assert len(after) == len(before) + 1
    # the previous entries survive untouched
    assert after[1:len(before) + 1] == before


def test_update_records_who_entered_it(logged_in, fresh_db):
    logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                data={"percent": 55, "status": "At risk", "note": "x"})
    # Read through the card, which names the person rather than their id.
    assert _diary(fresh_db, D1)[0]["EnteredBy"] == ELIZABETH_NAME


# --- validation -----------------------------------------------------------


@pytest.mark.parametrize("percent", [101, 250, -5])
def test_percent_outside_zero_to_one_hundred_is_refused(logged_in, fresh_db, percent):
    before = _count(fresh_db)
    response = logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                          data={"percent": percent, "status": "On track"})
    assert response.status_code == 422
    assert "between 0 and 100" in response.text
    assert _count(fresh_db) == before, "a refused write must not persist"


def test_unknown_status_is_refused(logged_in, fresh_db):
    before = _count(fresh_db)
    response = logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                          data={"percent": 10, "status": "Doing fine"})
    assert response.status_code == 422
    assert _count(fresh_db) == before


def test_note_over_the_limit_is_refused(logged_in, fresh_db):
    from app.repo import NOTE_MAX

    before = _count(fresh_db)
    response = logged_in("Elizabeth Smith").post(
        f"/major-initiatives/{D1}/updates",
        data={"percent": 10, "status": "On track", "note": "x" * (NOTE_MAX + 1)},
    )
    assert response.status_code == 422
    assert str(NOTE_MAX) in response.text
    assert _count(fresh_db) == before


def test_note_at_the_limit_is_accepted(logged_in, fresh_db):
    from app.repo import NOTE_MAX

    response = logged_in("Elizabeth Smith").post(
        f"/major-initiatives/{D1}/updates",
        data={"percent": 10, "status": "On track", "note": "x" * NOTE_MAX},
    )
    assert response.status_code == 200


def test_rule_errors_do_not_leak_sqlite(logged_in):
    """A refused write is a 422 with a message, never a driver exception."""
    response = logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                          data={"percent": 999, "status": "On track"})
    assert response.status_code == 422
    assert "sqlite3" not in response.text.lower()
    assert "integrityerror" not in response.text.lower()


# --- 6.4 server-side permission -------------------------------------------


def test_non_owner_posting_directly_gets_403(logged_in, fresh_db):
    before = _count(fresh_db)
    response = logged_in("Tim Jacobbe").post(f"/major-initiatives/{D1}/updates",
                                     data={"percent": 99, "status": "Complete"})
    assert response.status_code == 403
    assert _count(fresh_db) == before, "a 403 must not write"


def test_update_form_is_403_for_a_non_owner(logged_in):
    assert logged_in("Tim Jacobbe").get(f"/major-initiatives/{D1}/update").status_code == 403


def test_dean_and_admin_may_update_any_initiative(logged_in):
    assert logged_in("Bill Gaudelli").get(f"/major-initiatives/{D1}/update").status_code == 200
    assert logged_in("Kevin").get(f"/major-initiatives/{D1}/update").status_code == 200


def test_update_button_hidden_from_a_non_owner(logged_in):
    assert 'update-button' not in logged_in("Tim Jacobbe").get(f"/major-initiatives/{D1}").text


def test_update_button_shown_to_owner_dean_and_admin(logged_in):
    assert 'update-button' in logged_in("Elizabeth Smith").get(f"/major-initiatives/{D1}").text
    assert 'update-button' in logged_in("Bill Gaudelli").get(f"/major-initiatives/{D1}").text
    assert 'update-button' in logged_in("Kevin").get(f"/major-initiatives/{D1}").text


# --- no Dean rollup -------------------------------------------------------


def test_d1_update_does_not_change_the_dean_initiative(logged_in, fresh_db):
    from app import queries

    dean_before = queries.initiative_card(DEAN)["latest"]
    logged_in("Elizabeth Smith").post(f"/major-initiatives/{D1}/updates",
                                data={"percent": 80, "status": "At risk", "note": "big move"})
    dean_after = queries.initiative_card(DEAN)["latest"]
    assert dean_after == dean_before


def test_dean_update_is_independent_of_its_d1_children(logged_in):
    from app import queries

    d1_before = queries.initiative_card(D1)["latest"]
    logged_in("Bill Gaudelli").post(f"/major-initiatives/{DEAN}/updates",
                           data={"percent": 95, "status": "Off track"})
    assert queries.initiative_card(D1)["latest"] == d1_before


# --- form + response behaviour --------------------------------------------


def test_form_has_slider_select_and_capped_note(logged_in):
    from app.repo import NOTE_MAX

    body = logged_in("Elizabeth Smith").get(f"/major-initiatives/{D1}/update").text
    assert 'type="range"' in body
    assert 'min="0"' in body and 'max="100"' in body
    assert "<select" in body and "At risk" in body
    assert f'maxlength="{NOTE_MAX}"' in body


def test_successful_post_returns_the_card_and_signals_the_list(logged_in):
    response = logged_in("Elizabeth Smith").post(
        f"/major-initiatives/{D1}/updates", headers={"HX-Request": "true"},
        data={"percent": 55, "status": "At risk", "note": "halfway"},
    )
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "55%" in response.text
    assert D1 in response.headers.get("HX-Trigger", "")


def test_updates_to_a_retired_or_unknown_initiative_are_refused(logged_in):
    assert logged_in("Elizabeth Smith").post("/major-initiatives/NOPE-9/updates",
                                       data={"percent": 10, "status": "On track"}).status_code == 404


def test_updates_are_behind_the_gate(anon):
    response = anon.post(f"/major-initiatives/{D1}/updates",
                         data={"percent": 10, "status": "On track"}, follow_redirects=False)
    assert response.status_code == 303