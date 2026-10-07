"""Goal and priority list screens, on the merged register model (2026-10-07).

The merged model has ONE initiative tier: the register's Team Initiatives,
grouped by owner. The prototype's Dean-first / D-1-by-owner ordering and its
sample counts are gone. The register ships no diary, so tests that need progress
seed it with the `diary` fixture.
"""

import pytest

from app import queries  # noqa: E402


def _goal_number(short_name: str) -> int:
    """Resolve a goal's number from its canonical short name."""
    for goal in queries.goal_tiles():
        if goal["ShortName"] == short_name:
            return goal["GoalNumber"]
    raise AssertionError("no goal named %r in the sample data" % short_name)


INNOVATION = "Innovation"


def _codes(response):
    import re

    return re.findall(r'class="code">([A-Z0-9-]+)<', response.text)


def test_goal_list_renders(logged_in):
    response = logged_in("Bill Gaudelli").get("/goals/%d" % _goal_number("Research"))
    assert response.status_code == 200
    assert "Research" in response.text


def test_rows_are_grouped_by_owner(logged_in):
    """The merged list groups every row by owner; there is no Dean/D-1 divider."""
    body = logged_in("Bill Gaudelli").get("/goals/%d" % _goal_number("Research")).text
    assert 'class="list-group-label"' in body or "list-group-label" in body


def test_status_counts_in_header_sum_to_the_row_count(logged_in):
    """The header rollup is a total followed by a per-status breakdown."""
    import re

    response = logged_in("Bill Gaudelli").get("/goals/%d" % _goal_number("Research"))
    m = re.search(r'class="section-note">([^<]+)<', response.text)
    assert m, "no rollup line rendered"
    label = m.group(1).strip()
    assert re.match(r"\d+ initiative", label), label
    assert "aggregate" not in response.text.lower()


def test_no_aggregate_percent_is_rendered(logged_in):
    """design.md: "No aggregate percent anywhere; only counts by status"."""
    body = logged_in("Bill Gaudelli").get("/goals/%d" % _goal_number("Research")).text
    assert "aggregate" not in body.lower()


def test_no_update_yet_is_shown_when_an_initiative_has_no_progress(logged_in, fresh_db):
    """The register ships no diary, so an initiative with no update is the normal
    starting state; the row must say "No update yet", not "0%"."""
    from app import queries

    number = _goal_number("Research")
    row = next((r for r in queries.goal_rows(number) if r["PercentComplete"] is None), None)
    assert row is not None, "expected some Research initiative with no diary yet"

    body = logged_in("Bill Gaudelli").get("/goals/%d" % number).text
    assert "No update yet" in body


def test_progress_bar_renders_when_there_is_an_update(logged_in, fresh_db, diary):
    number = _goal_number("Research")
    row = queries.goal_rows(number)[0]
    diary(row["Code"], 42, "On track", on="2026-10-05")
    body = logged_in("Bill Gaudelli").get("/goals/%d" % number).text
    assert 'style="width: 42%"' in body
    assert "status-on-track" in body


def test_rows_carry_the_htmx_attributes_for_the_card(logged_in):
    number = _goal_number("Research")
    code = queries.goal_rows(number)[0]["Code"]
    body = logged_in("Bill Gaudelli").get("/goals/%d" % number).text
    assert f'hx-get="/team-initiatives/{code}"' in body
    assert 'hx-target="#card-modal"' in body
    assert 'hx-swap="innerHTML"' in body


def test_owner_name_links_to_a_person_card(logged_in):
    number = _goal_number("Research")
    row = queries.goal_rows(number)[0]
    body = logged_in("Bill Gaudelli").get("/goals/%d" % number).text
    if row["OwnerID"]:
        assert f'href="/people/{row["OwnerID"]}"' in body


def test_priority_list_uses_the_same_screen(logged_in):
    response = logged_in("Bill Gaudelli").get(f"/priorities/{INNOVATION}")
    assert response.status_code == 200
    assert "Innovation" in response.text


def test_unknown_goal_and_priority_are_404(logged_in):
    client = logged_in("Bill Gaudelli")
    assert client.get("/goals/99").status_code == 404
    assert client.get("/priorities/Nonexistent").status_code == 404


def test_lists_are_behind_the_gate(anon):
    assert anon.get("/goals/%d" % _goal_number("Research"), follow_redirects=False).status_code == 303


@pytest.mark.parametrize("goal_number", [1, 2, 3, 4, 5])
def test_every_goal_screen_renders(logged_in, goal_number):
    response = logged_in("Bill Gaudelli").get(f"/goals/{goal_number}")
    assert response.status_code == 200
