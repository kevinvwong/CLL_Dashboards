"""The portfolio dashboard home (blueprint-redesign scope correction).

Replaces test_blueprint_home.py's stage assertions: the hero stage was removed
because the instruction is to design our own, not replicate the prototype's
shape. What is asserted now is the dashboard, AND that every field the
prototype carries is present.
"""
import html as _html
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _home(logged_in):
    return _html.unescape(logged_in("Bill Gaudelli").get("/").text)


def _page(logged_in, path):
    return _html.unescape(logged_in("Bill Gaudelli").get(path).text)


# --- the dashboard, not the prototype's stage -------------------------------


def test_the_home_is_a_landing_not_a_stage(logged_in):
    """The home is a landing (overview split, 2026-10-07): health + stat band +
    the four-lens block. The lens card grids moved to their own pages."""
    body = _home(logged_in)
    assert "stat-band" in body
    assert "lens-grid" in body, "the four-lens block is missing"
    # The lens grids are no longer on the landing.
    assert "goal-grid" not in body
    assert "priority-grid" not in body
    assert "team-grid" not in body
    # Each lens page carries its own grid.
    assert "goal-grid" in _page(logged_in, "/goals")
    assert "oct16-grid" in _page(logged_in, "/outcomes")   # the six priorities
    assert "team-grid" in _page(logged_in, "/teams")
    # The 29-row table has its own page.
    assert "mi-table" not in body, "the landing still renders the MI table"
    assert "mi-table" in _page(logged_in, "/team-initiatives")
    # The prototype's stage is gone.
    assert "dean-node" not in body, "the Dean node stage still renders"
    assert "priority-map" not in body, "the prototype's priority map still renders"


def test_the_stat_band_reports_the_portfolio(logged_in):
    body = _home(logged_in)
    for label in ("Initiatives", "Priorities", "Teams", "Team Initiatives", "Need review"):
        assert label in body, "missing stat %s" % label


# --- every field the prototype carries --------------------------------------


def test_all_six_priorities_render(logged_in):
    """The six priorities render on /outcomes (the canonical page; /priorities
    redirects). The wireframes called them "outcomes"."""
    from app import queries
    body = _page(logged_in, "/outcomes")
    assert body.count('class="oct16-card') == 6
    for p in queries.blueprint_priorities():
        assert p["Title"] in body


def test_priority_cards_carry_the_governed_fields(logged_in):
    """Measure, target, cadence and owner - the four we did not hold before.

    They live on the priority page now, not inline on the overview card
    (interconnection-redesign 5: the overview is compact and links out).
    """
    from app import queries
    p = queries.blueprint_priorities()[0]
    body = _page(logged_in, "/priorities/" + p["Name"])
    for label in ("Measure", "Target", "Cadence", "Owner"):
        assert label in body, "priority page missing %s" % label


def test_a_priorities_measure_target_and_cadence_actually_render(logged_in):
    """Not just the label: the prototype's own values."""
    from app import queries
    p = next(x for x in queries.blueprint_priorities() if x["Code"] == "P01")
    body = _page(logged_in, "/priorities/" + p["Name"])
    assert p["Measure"] in body
    assert p["Target"][:40] in body
    assert p["Cadence"] in body


def test_the_four_teams_render_with_descriptions(logged_in):
    body = _page(logged_in, "/teams")
    assert body.count("team-card") == 4
    for team in ("Learning Experiences", "Learning Ecosystems",
                 "Learning Infrastructure", "Learning Futures"):
        assert team in body


def test_all_29_team_initiatives_render_with_their_fields(logged_in):
    from app import queries
    body = _page(logged_in, "/team-initiatives")
    rows = queries.team_initiative_cards()
    assert len(rows) == 29
    assert body.count('class="mi-row"') == 29
    # The table's columns cover the prototype's fields. The first column is the
    # canon's stable key (MI-###) as of interconnection-redesign 4.2: the row
    # key is now the identifier the source register uses, not our internal code.
    # "Source area" was removed from this list on 2026-10-09: D-009 / FR-009 hide
    # it from standard views while retaining it in the store.
    for col in ("ID", "Team Initiative", "Team", "Strategy alignment",
                "Initiatives", "Target", "Target status", "Feeds"):
        assert col in body, "missing column %s" % col


def test_a_team_initiative_shows_its_team_and_priorities(logged_in):
    from app import queries
    body = _page(logged_in, "/team-initiatives")
    k = queries.team_initiative_cards()[0]
    assert k["Team"] in body
    # Its priority codes appear as chips.
    for p in k["priorities"]:
        assert p["Code"] in body


def test_source_area_is_retained_but_not_rendered(logged_in):
    """D-009 / FR-009 / CR-011: hidden from standard views, kept in the store.

    This inverts an earlier assertion that required Source Area ON screen. The
    authoritative meeting record supersedes it: the field is lineage, not
    something a reader acts on. Both halves are asserted, because "hidden" is
    only half the decision - deleting the data would also satisfy the first.
    """
    from app import queries
    body = _page(logged_in, "/team-initiatives")
    k = queries.team_initiative_cards()[0]
    assert k["SourceArea"], "SourceArea must still be queried off the row"
    assert k["SourceArea"] not in body, "Source Area must not be rendered (D-009)"
    assert "Source area" not in body, "no Source Area column header (D-009)"


def test_the_needs_review_marker_is_shown(logged_in):
    from app import queries
    body = _page(logged_in, "/team-initiatives")
    needs = [k for k in queries.team_initiative_cards() if k["TargetStatus"] == "needs_review"]
    assert needs, "expected some Team Initiatives needing review"
    assert "needs review" in body


def test_no_aggregate_performance_figure(logged_in):
    """The design forbids a rollup score; counts only.

    Note: the word "average" legitimately appears inside the P04 target text
    ("keep average non-degree development at 28 days or less") - that is the
    prototype's own wording, not a computed figure. So this asserts the absence
    of a computed aggregate element, not of the word.
    """
    body = _home(logged_in)
    assert "aggregate" not in body.lower()
    # No element is a combined or averaged score.
    assert "rollup-score" not in body
    assert "combined-score" not in body
    assert "percent-complete-total" not in body


# --- the authoritative meeting record: CR-003, CR-005 ------------------------------------------

def test_the_register_offers_list_and_card_views(logged_in):
    """CR-003 / FR-007: both presentations, one drill-down rule."""
    body = _page(logged_in, "/team-initiatives")
    assert 'data-view-choice="list"' in body
    assert 'data-view-choice="card"' in body
    # Real controls carrying pressed state, not styled divs.
    assert 'aria-pressed="true"' in body and 'aria-pressed="false"' in body
    # The card rendering carries the same hx-get as the list row, so selecting a
    # Team Initiative opens the same drawer either way (FR-002, no dead ends).
    assert 'class="mi-card-grid"' in body


def test_the_view_is_shareable_in_the_url(logged_in):
    """AC-009 / CR-018: a presenter who switches view hands over a link in it.

    That is why ?view= is authoritative and the stored preference is only a
    fallback - a purely client-side preference cannot travel to the next person.
    """
    assert 'data-mi-view="list"' in _page(logged_in, "/team-initiatives")
    assert 'data-mi-view="list"' in _page(logged_in, "/team-initiatives?view=list")
    assert 'data-mi-view="card"' in _page(logged_in, "/team-initiatives?view=card")


def test_the_default_view_follows_density():
    """A filtered subset reads better as cards; the whole 29-row register does not.

    The default is computed server-side from the ROW COUNT, and only when the URL
    expresses no preference. It is deliberately not re-derived as filters change:
    a view that moves under a reader is worse than one that is merely suboptimal.
    """
    from app.main import MI_CARD_THRESHOLD, resolve_mi_view
    assert resolve_mi_view(None, 29) == "list", "the full register is the dense case"
    assert resolve_mi_view(None, 4) == "card", "a filtered subset is the sparse case"
    assert resolve_mi_view(None, MI_CARD_THRESHOLD) == "card"
    assert resolve_mi_view(None, MI_CARD_THRESHOLD + 1) == "list"
    # An explicit choice always wins, whatever the density.
    assert resolve_mi_view("card", 29) == "card"
    assert resolve_mi_view("list", 4) == "list"
    # Junk falls back to the density default rather than an unknown view.
    assert resolve_mi_view("bogus", 29) == "list"


def test_goal_views_show_the_full_strategy_2035_language(logged_in):
    """FR-003 / CR-005 / AC-006: the canonical sentence, not "Academic".

    The short label survives as a supporting eyebrow, so this asserts the full
    language is present as the card title rather than that the short one is gone.
    """
    from app import queries
    body = _page(logged_in, "/goals")
    goals = queries.goal_tiles()
    assert goals, "expected the five Strategy 2035 goals"
    for g in goals:
        assert g["FullName"], "Goal %s has no canonical title loaded" % g["GoalNumber"]
        assert g["FullName"] in body, "goal %s full language missing" % g["GoalNumber"]