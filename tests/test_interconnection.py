"""The interconnection surface (interconnection-redesign group 3-4).

The edges the canon states and the schema now holds, browsable from both
directions, with no dead-end route: /teams/{id} and /team-initiatives/{mi_id}.

`logged_in` is a factory fixture: `logged_in("Bill Gaudelli")` -> a signed-in client.
"""
import html

import pytest


@pytest.fixture
def page(logged_in):
    """A signed-in client, resolved once so cases read `page.get(...)`."""
    return logged_in("Bill Gaudelli")


def _text(r):
    """Response text with entities decoded, so a title with `&` matches.

    Jinja autoescapes, so 'Portfolio & pathways' renders as 'Portfolio &amp;
    pathways'. A test that asserts the raw title must decode first.
    """
    return html.unescape(r.text)


# --- the new routes exist and render ----------------------------------------


def test_every_team_has_a_page(page):
    from app import queries
    for t in queries.team_overview():
        r = page.get("/teams/%d" % t["TeamID"])
        assert r.status_code == 200, "team %s" % t["Name"]
        assert t["Name"] in r.text


def test_every_team_initiative_has_a_page_by_mi_id(page):
    from app import queries
    mis = queries.team_initiative_cards()
    assert len(mis) == 29
    for k in mis:
        key = k["MIId"] or k["Code"]
        r = page.get("/team-initiatives/%s" % key)
        assert r.status_code == 200, "mi %s" % key
        assert k["Title"] in _text(r)


def test_a_team_initiative_is_reachable_by_its_old_code(page):
    """The code we held before the canon is kept as a fallback key."""
    from app import queries
    k = queries.team_initiative_cards()[0]
    r = page.get("/team-initiatives/%s" % k["Code"])
    assert r.status_code == 200
    assert k["Title"] in _text(r)


def test_a_team_page_lists_its_team_initiatives(page):
    from app import queries
    t = queries.team_overview()[0]
    r = page.get("/teams/%d" % t["TeamID"])
    for k in t["team_initiatives"]:
        assert k["Title"] in _text(r)


def test_an_unknown_team_is_a_404(page):
    assert page.get("/teams/99999").status_code == 404


def test_an_unknown_team_initiative_is_a_404(page):
    assert page.get("/team-initiatives/MI-999").status_code == 404


# --- the edge is traversable both ways ---------------------------------------


def test_a_team_initiative_page_links_to_its_goals(page):
    """The MI -> Goal edge, rendered from the initiative side."""
    from app import queries
    k = queries.team_initiative_cards()[0]
    r = page.get("/team-initiatives/%s" % (k["MIId"] or k["Code"]))
    for g in k["goals"]:
        assert "/goals/%d" % g["GoalNumber"] in r.text


def test_a_goal_page_lists_the_team_initiatives_aligned_to_it(page):
    """The same edge, from the goal side."""
    from app import queries
    r = page.get("/goals/5")
    assert r.status_code == 200
    mis = queries.goal_team_initiatives(5)
    assert mis, "goal 5 should have aligned Team Initiatives"
    for k in mis:
        assert k["Title"] in _text(r)


def test_a_team_initiative_page_links_to_its_team(page):
    from app import queries
    k = [x for x in queries.team_initiative_cards() if x["TeamID"]][0]
    r = page.get("/team-initiatives/%s" % (k["MIId"] or k["Code"]))
    assert "/teams/%d" % k["TeamID"] in r.text


def test_a_team_initiative_page_links_to_its_priorities(page):
    from app import queries
    k = [x for x in queries.team_initiative_cards() if x["priorities"]][0]
    r = page.get("/team-initiatives/%s" % (k["MIId"] or k["Code"]))
    for p in k["priorities"]:
        assert "/priorities/" in r.text


# --- the home regression is closed -------------------------------------------


def test_the_goals_page_links_to_every_goal(page):
    r = page.get("/goals")
    for n in range(1, 6):
        assert "/goals/%d" % n in r.text, "/goals does not link to goal %d" % n


def test_the_goals_page_has_a_goals_section(page):
    r = page.get("/goals")
    assert 'id="goals"' in r.text or "The five goals" in r.text


def test_the_overview_no_longer_carries_the_mi_table(page):
    """The cut: the overview was 56 KB, two-thirds of it the 29-row table, and
    every row rendered twice. The table moved to /team-initiatives and the section here is
    a link, not the table."""
    r = page.get("/")
    assert 'class="mi-row"' not in r.text, "the overview still renders MI rows"
    assert 'class="mi-table"' not in r.text, "the overview still renders the table"
    # It still points at the table and the needs-review view.
    assert 'href="/team-initiatives"' in r.text
    assert 'href="/team-initiatives?target=needs_review"' in r.text


def test_the_overview_has_no_duplicated_mi_list(page):
    """The landing lists no initiatives directly; each lens links out. (Overview
    split 2026-10-07: the lens grids left the landing for their own pages.)"""
    from app import queries
    r = page.get("/")
    assert 'class="mi-title"' not in r.text
    for t in queries.team_overview():
        assert 'href="/teams/%d"' % t["TeamID"] in page.get("/teams").text


# --- the MI table filter and grouping ----------------------------------------


def test_mi_table_keys_rows_by_mi_id(page):
    from app import queries
    r = page.get("/team-initiatives")
    for k in queries.team_initiative_cards():
        assert "/team-initiatives/%s" % k["MIId"] in r.text


def test_needs_review_filter_returns_only_those(page):
    from app import queries
    r = page.get("/team-initiatives?target=needs_review")
    assert r.status_code == 200
    all_team_initiatives = queries.team_initiative_cards()
    needs = [k for k in all_team_initiatives if k["TargetStatus"] == "needs_review"]
    assert len(needs) == 21, "the canon marks 21 of 29 for review"
    # The filtered table renders only the needs-review rows.
    assert r.text.count('class="mi-row"') == len(needs)
    assert r.text.count('class="mi-row"') < len(all_team_initiatives)


def test_group_by_team_renders_group_labels(page):
    r = page.get("/team-initiatives?group=team")
    assert r.status_code == 200
    assert 'class="group-row"' in r.text


def test_group_by_source_area_renders_group_labels(page):
    r = page.get("/team-initiatives?group=source_area")
    assert r.status_code == 200
    assert 'class="group-row"' in r.text


def test_an_unknown_filter_is_ignored_not_errored(page):
    r = page.get("/team-initiatives?target=bogus&group=bogus")
    assert r.status_code == 200
    from app import queries
    assert r.text.count('class="mi-row"') == len(queries.team_initiative_cards())


# --- search finds the new pages ----------------------------------------------


def test_a_team_initiative_is_reachable_by_its_mi_id_in_search(page):
    """A user who knows the register's key must be able to find it."""
    from app import queries
    k = queries.team_initiative_cards()[0]
    r = page.get("/search", params={"q": k["MIId"]})
    assert r.status_code == 200
