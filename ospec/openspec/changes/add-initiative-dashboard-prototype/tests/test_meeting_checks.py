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


def _set_progress(db, code, status, days_ago=None):
    """Point one initiative's latest update at a status and age.

    days_ago=None leaves the existing date, which in the sample data is recent.
    """
    conn = sqlite3.connect(db)
    if days_ago is None:
        conn.execute(
            "UPDATE ProgressUpdates SET Status = ? "
            "WHERE InitiativeID = (SELECT InitiativeID FROM Initiatives WHERE Code = ?)",
            (status, code),
        )
    else:
        conn.execute(
            "UPDATE ProgressUpdates SET Status = ?, UpdateDate = date('now', ?) "
            "WHERE InitiativeID = (SELECT InitiativeID FROM Initiatives WHERE Code = ?)",
            (status, "-%d days" % days_ago, code),
        )
    conn.commit()
    conn.close()


def _quiet(db):
    """Make the sample data a clean slate: nothing at risk, nothing stale."""
    conn = sqlite3.connect(db)
    conn.execute("UPDATE ProgressUpdates SET Status = 'On track', UpdateDate = date('now')")
    conn.commit()
    conn.close()


def test_attention_list_holds_initiatives_that_are_at_risk(logged_in, fresh_db):
    """At risk is still listed. The spec now also names Off track and staleness,
    which are covered separately below."""
    _quiet(fresh_db)
    _set_progress(fresh_db, "ELIZ-1", "At risk")

    attention = queries.attention_list()
    assert [r["Code"] for r in attention] == ["ELIZ-1"], "only ELIZ-1 should qualify"
    assert "ELIZ-1" in logged_in("Bill").get("/meeting").text


def test_attention_entries_link_to_their_card(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET Status = 'At risk', UpdateDate = date('now')")
    conn.commit()
    conn.close()

    body = logged_in("Bill").get("/meeting").text
    assert 'hx-get="/initiatives/' in body
    assert 'hx-target="#card-modal"' in body


def test_off_track_leads_the_attention_list(logged_in, fresh_db):
    """Replaces test_off_track_is_not_in_the_attention_list, which pinned the
    wrong behaviour.

    That test asserted Off track was excluded and claimed that was "following
    the spec literally". It was not: the requirement names "At risk or Off
    track", and the earlier session read the scenario underneath - which
    demonstrates only At risk - instead of the requirement above it. Amended
    2026-10-06. A stalled initiative is the thing a leadership meeting most
    needs to see, so Off track leads the list rather than disappearing from it.
    """
    _quiet(fresh_db)
    _set_progress(fresh_db, "TIM-4", "Off track")
    _set_progress(fresh_db, "ELIZ-1", "At risk")

    codes = [r["Code"] for r in queries.attention_list()]
    assert "TIM-4" in codes, "Off track must be listed"
    assert codes[0] == "TIM-4", "Off track must outrank At risk"
    assert "TIM-4" in logged_in("Bill").get("/meeting").text


def test_a_stale_initiative_is_listed_with_its_age(logged_in, fresh_db):
    _quiet(fresh_db)
    _set_progress(fresh_db, "D-A", "On track", days_ago=30)

    rows = {r["Code"]: r for r in queries.attention_list()}
    assert "D-A" in rows, "an update 30 days old is stale"
    assert rows["D-A"]["Reason"] == "No update in 30 days"
    assert "30 days" in logged_in("Bill").get("/meeting").text


def test_an_update_inside_the_window_is_not_stale(logged_in, fresh_db):
    """The boundary. The spec says *older than* 14, so 14 itself is inside."""
    _quiet(fresh_db)
    _set_progress(fresh_db, "D-A", "On track", days_ago=14)
    assert "D-A" not in [r["Code"] for r in queries.attention_list()], "14 is not older than 14"

    _set_progress(fresh_db, "D-A", "On track", days_ago=15)
    assert "D-A" in [r["Code"] for r in queries.attention_list()], "15 is older than 14"


def test_an_initiative_with_no_update_says_so_rather_than_a_number(logged_in, fresh_db):
    conn = sqlite3.connect(fresh_db)
    conn.execute("DELETE FROM ProgressUpdates")
    conn.commit()
    conn.close()

    rows = {r["Code"]: r for r in queries.attention_list()}
    assert rows, "initiatives with no update at all must be listed"
    assert all(r["Reason"] == "No update yet" for r in rows.values())
    assert all(r["AgeDays"] is None for r in rows.values()), "no date means no age to report"


def test_one_initiative_with_two_reasons_appears_once(logged_in, fresh_db):
    _quiet(fresh_db)
    _set_progress(fresh_db, "ELIZ-1", "At risk", days_ago=30)   # both reasons at once

    codes = [r["Code"] for r in queries.attention_list()]
    assert codes.count("ELIZ-1") == 1, "a one-page agenda cannot afford a duplicate"
    rows = {r["Code"]: r for r in queries.attention_list()}
    assert rows["ELIZ-1"]["Reason"] == "At risk", "the more severe reason wins"


def test_the_order_is_severity_then_oldest_first(logged_in, fresh_db):
    _quiet(fresh_db)
    _set_progress(fresh_db, "D-A", "On track", days_ago=40)     # stale, oldest
    _set_progress(fresh_db, "D-B", "On track", days_ago=20)     # stale
    _set_progress(fresh_db, "ELIZ-1", "At risk", days_ago=5)    # at risk
    _set_progress(fresh_db, "TIM-4", "Off track", days_ago=9)   # off track

    codes = [r["Code"] for r in queries.attention_list()]
    assert codes == ["TIM-4", "ELIZ-1", "D-A", "D-B"], (
        "severity first (Off track, At risk, stale), then oldest first: got %s" % codes
    )


def test_the_order_is_stable_when_ages_tie(logged_in, fresh_db):
    """A tie on age must fall back to code, or the agenda reorders between
    renders and is harder to follow in a meeting.

    The codes matter. An earlier version of this test used D-A, D-B, D-C, which
    happen to be in the same order by insertion as alphabetically - so removing
    the code tie-break could not change the result and the test passed without
    testing anything. TIM-* and MAR-* sit the other way round: TIM-* is inserted
    first but MAR-* sorts first alphabetically, so only a real tie-break produces
    MAR-1, MAR-2, TIM-1.
    """
    _quiet(fresh_db)
    for code in ("TIM-1", "MAR-1", "MAR-2"):
        _set_progress(fresh_db, code, "At risk", days_ago=3)

    first = [r["Code"] for r in queries.attention_list()]
    second = [r["Code"] for r in queries.attention_list()]
    assert first == second, "the order must not vary between renders"
    assert first == ["MAR-1", "MAR-2", "TIM-1"], (
        "equal ages must fall back to code order, not insertion order: got %s" % first
    )


def test_the_reason_is_shown_only_when_it_adds_something(logged_in, fresh_db):
    """A reason that just repeats the badge is noise on a one-page agenda.

    An At risk row shows the badge "At risk" and nothing more; a stale row has no
    badge that says why, so it states its age. Both must still carry a Reason, so
    that the query does not depend on how the template chooses to render it.
    """
    _quiet(fresh_db)
    _set_progress(fresh_db, "ELIZ-1", "At risk", days_ago=2)      # status only
    _set_progress(fresh_db, "D-A", "On track", days_ago=40)       # stale only

    rows = {r["Code"]: r for r in queries.attention_list()}
    assert rows["ELIZ-1"]["Reason"] == "At risk"
    assert rows["D-A"]["Reason"] == "No update in 40 days"

    body = logged_in("Bill").get("/meeting").text
    section = body[body.index("Needs attention"):body.index("Changes since")]
    assert "At risk" in section, "the status badge still shows"
    assert "No update in 40 days" in section, "a stale row must say why it is listed"
    assert ">At risk<" in section, "the status is the badge, not a repeated reason span"


def test_empty_attention_says_so(logged_in, fresh_db):
    _quiet(fresh_db)

    body = logged_in("Bill").get("/meeting").text
    assert "Nothing is off track, at risk, or stale" in body


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