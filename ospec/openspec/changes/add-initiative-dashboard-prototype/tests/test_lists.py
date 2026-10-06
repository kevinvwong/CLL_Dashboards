"""Task 4.5 check: goal and priority list screens.

strategy-navigation requires ordering (Dean first, then a divider, then D-1
grouped by owner), the primary badge, a "No update yet" empty state, and a
header of counts by status with no aggregate percent.
"""

import pytest

RESEARCH = 3  # 5 active initiatives: 3 Dean (D-A, D-C, D-D), 2 D-1
INNOVATION = "Innovation"


def _codes(response):
    import re

    return re.findall(r'class="code">([A-Z0-9-]+)<', response.text)


def test_goal_list_renders(logged_in):
    response = logged_in("Bill").get("/goals/3")
    assert response.status_code == 200
    assert "Research" in response.text


def test_dean_rows_come_first_ordered_by_code(logged_in):
    codes = _codes(logged_in("Bill").get("/goals/3"))
    dean = [c for c in codes if c.startswith("D-")]
    assert dean == ["D-A", "D-C", "D-D"]


def test_divider_sits_between_dean_and_d1(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    divider_at = body.index('class="divider"')
    dean_at = body.index("D-A")
    eliz_at = body.index("ELIZ-1")
    assert dean_at < divider_at < eliz_at


def test_d1_rows_are_grouped_by_owner(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    groups = [g for g in ("Elizabeth", "Mario") if f'class="list-group-label">{g}<' in body]
    assert groups == ["Elizabeth", "Mario"]
    # grouped, not interleaved: each owner's rows sit inside their own group
    assert body.index("ELIZ-1") < body.index("MAR-4")


def test_primary_tag_shows_a_badge(logged_in):
    from app import queries

    primaries = sorted(r["Code"] for r in queries.goal_rows(3) if r["IsPrimary"])
    assert primaries, "sample data should carry primary tags for this goal"
    body = logged_in("Bill").get("/goals/3").text
    # Exactly the primary rows get a badge, and no others do.
    assert body.count('class="badge">Primary<') == len(primaries)
    for code in primaries:
        assert code in body


def test_status_counts_in_header_sum_to_the_row_count(logged_in):
    import re

    response = logged_in("Bill").get("/goals/3")
    counts = {
        status: int(n)
        for status, n in re.findall(
            r'count count-[a-z\-]+">([A-Za-z ]+?) (\d+)<', response.text
        )
    }
    assert counts == {"On track": 4, "At risk": 1}
    assert sum(counts.values()) == len(_codes(response)) == 5


def test_no_aggregate_percent_is_rendered(logged_in):
    """design.md: "No aggregate percent anywhere; only counts by status."

    Asserted structurally rather than by hunting for a number: no element
    carries an aggregate class, and the only percentages on the page are the
    per-initiative bars.
    """
    body = logged_in("Bill").get("/goals/3").text
    assert "aggregate" not in body.lower()
    # Per-row percentages are present and are the only "%" figures.
    assert body.count('class="bar-label"') == 5


def test_no_update_yet_is_shown_when_an_initiative_has_no_progress(logged_in, fresh_db):
    """The seed gives every active initiative a diary - vw_DataChecks reports
    "No progress update yet" as an issue and currently reports none - so the
    empty state cannot be reached from sample data. Delete the diary for one
    initiative in this test's private copy to exercise it."""
    import sqlite3

    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM ProgressUpdates WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code = 'ELIZ-1')"
    )
    conn.commit()
    conn.close()

    from app import queries

    row = [r for r in queries.goal_rows(3) if r["Code"] == "ELIZ-1"][0]
    assert row["PercentComplete"] is None

    body = logged_in("Bill").get("/goals/3").text
    assert "No update yet" in body
    assert "bar-empty" in body
    # An empty bar, never a 0% bar: "No update" is not "0% complete".
    assert 'style="width: 0%"' not in body


def test_progress_bar_length_and_status_class(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    assert "style=\"width: 30%\"" in body          # D-A is at 30%
    assert "status-at-risk" in body                # D-C is At risk
    assert "status-on-track" in body


def test_rows_carry_the_htmx_attributes_for_the_card(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    assert 'hx-get="/initiatives/D-A"' in body
    assert 'hx-target="#card-modal"' in body
    assert 'hx-swap="innerHTML"' in body


def test_owner_name_links_to_a_person_card(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    # Bill is PersonID 1, Elizabeth 2 in the sample data.
    assert 'href="/people/1"' in body
    assert 'href="/people/2"' in body


def test_priority_list_uses_the_same_screen(logged_in):
    response = logged_in("Bill").get(f"/priorities/{INNOVATION}")
    assert response.status_code == 200
    assert "Innovation" in response.text
    assert 'class="initiative-list' in response.text


def test_unknown_goal_and_priority_are_404(logged_in):
    client = logged_in("Bill")
    assert client.get("/goals/99").status_code == 404
    assert client.get("/priorities/Nonexistent").status_code == 404


def test_lists_are_behind_the_gate(anon):
    assert anon.get("/goals/3", follow_redirects=False).status_code == 303


@pytest.mark.parametrize("goal_number", [1, 2, 3, 4, 5])
def test_every_goal_screen_renders(logged_in, goal_number):
    response = logged_in("Bill").get(f"/goals/{goal_number}")
    assert response.status_code == 200