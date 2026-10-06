"""Tasks 8.5 and 8.6 checks: the meeting page and the data-checks page.

meeting-view requires a date window, an attention list, and a print output
carrying only the agenda. data-intake requires /checks to name each issue and
link it to the initiative.
"""

import sqlite3

import pytest

from app import queries


# --- 8.5 meeting window ---------------------------------------------------


def test_meeting_defaults_to_the_last_seven_days(logged_in):
    response = logged_in("Bill").get("/meeting")
    assert response.status_code == 200
    assert queries.default_since() in response.text


def test_since_parameter_narrows_the_window(logged_in, fresh_db):
    """An update dated before the window must not appear in the changes list.

    Scoped to the changes section on purpose: the attention list is not
    windowed, so an at-risk initiative still shows its (old) last-update date
    there, and a whole-page assertion would pass for the wrong reason.
    """
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET UpdateDate = '2020-01-01'")
    conn.commit()
    conn.close()

    def changes_section(text):
        return text[text.index("Changes since"):]

    wide = logged_in("Bill").get("/meeting?since=2000-01-01").text
    assert "2020-01-01" in changes_section(wide), "a wide window should show the old update"

    narrow = logged_in("Bill").get("/meeting").text
    assert "2020-01-01" not in changes_section(narrow), (
        "the default 7-day window must exclude it"
    )


def test_since_is_echoed_back(logged_in):
    response = logged_in("Bill").get("/meeting?since=2026-09-30")
    assert "2026-09-30" in response.text


def test_bad_since_is_rejected_rather_than_crashing(logged_in):
    assert logged_in("Bill").get("/meeting?since=not-a-date").status_code in (200, 422, 400)


def test_changes_are_grouped_by_owner(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET UpdateDate = date('now')")
    conn.commit()
    conn.close()

    body = logged_in("Bill").get("/meeting?since=2000-01-01").text
    assert 'class="list-group-label"' in body
    assert "Changes since" in body


# --- 8.5 attention list ---------------------------------------------------


def test_attention_list_holds_initiatives_that_are_at_risk(logged_in, fresh_db):
    """The spec names At risk and only At risk."""
    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "UPDATE ProgressUpdates SET Status = 'At risk', UpdateDate = date('now') "
        "WHERE InitiativeID = (SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1')"
    )
    conn.commit()
    conn.close()

    attention = queries.attention_list()
    assert "ELIZ-1" in [r["Code"] for r in attention]
    # Every entry is at risk, and nothing else is.
    assert all(r["Status"] == "At risk" for r in attention)
    assert "ELIZ-1" in logged_in("Bill").get("/meeting").text


def test_attention_entries_link_to_their_card(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET Status = 'At risk', UpdateDate = date('now')")
    conn.commit()
    conn.close()

    body = logged_in("Bill").get("/meeting").text
    assert 'hx-get="/initiatives/' in body
    assert 'hx-target="#card-modal"' in body


def test_off_track_is_not_in_the_attention_list(logged_in, fresh_db):
    """Documented consequence of following the spec literally: Off track,
    which is arguably more urgent, is excluded. Pinned so a future change is
    deliberate."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET Status = 'Off track', UpdateDate = date('now')")
    conn.commit()
    conn.close()

    assert queries.attention_list() == []


def test_empty_attention_says_so(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET Status = 'On track', UpdateDate = date('now')")
    conn.commit()
    conn.close()

    assert "Nothing is at risk" in logged_in("Bill").get("/meeting").text


# --- 8.5 print ------------------------------------------------------------


def test_print_output_carries_only_the_agenda(logged_in):
    """print.css hides the chrome; the page must therefore contain only the
    attention list and the change list as its sections."""
    body = logged_in("Bill").get("/meeting").text
    assert 'class="since-form no-print"' in body, "the date control must be marked no-print"
    print_css = open("app/static/print.css", encoding="utf-8").read()
    assert ".no-print" in print_css
    assert ".site-header" in print_css
    assert "Needs attention" in body
    assert "Changes since" in body


# --- 8.6 checks page ------------------------------------------------------


def test_checks_page_renders(logged_in):
    response = logged_in("Bill").get("/checks")
    assert response.status_code == 200


def test_checks_lists_each_issue_with_its_initiative(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM InitiativeLinks WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1')"
    )
    conn.commit()
    conn.close()

    issues = queries.data_checks()
    assert issues, "removing the link must produce a data-check issue"
    body = logged_in("Bill").get("/checks").text
    for issue in issues:
        assert issue["Code"] in body
        assert issue["Issue"] in body


def test_checks_uses_the_spec_wording_for_a_missing_dean_link(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM InitiativeLinks WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1')"
    )
    conn.commit()
    conn.close()

    issues = queries.data_checks()
    assert "D-1 initiative not linked to any Dean initiative" in [i["Issue"] for i in issues]


def test_checks_is_clear_on_clean_sample_data(logged_in):
    """build_db.py reports 0 issues, so the page must say so rather than
    showing an empty table."""
    body = logged_in("Bill").get("/checks").text
    assert queries.data_checks() == []
    assert "No issues" in body


def test_checks_rows_link_to_the_initiative(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM InitiativeLinks WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code='ELIZ-1')"
    )
    conn.commit()
    conn.close()

    body = logged_in("Bill").get("/checks").text
    assert 'hx-get="/initiatives/ELIZ-1"' in body


# --- gating ---------------------------------------------------------------


@pytest.mark.parametrize("path", ["/meeting", "/checks"])
def test_meeting_and_checks_are_behind_the_gate(anon, path):
    assert anon.get(path, follow_redirects=False).status_code == 303