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
    return _html.unescape(logged_in("Bill").get("/").text)


# --- the dashboard, not the prototype's stage -------------------------------


def test_the_home_is_a_dashboard_not_a_stage(logged_in):
    body = _home(logged_in)
    # The dashboard's parts.
    assert "stat-band" in body
    assert "priority-grid" in body
    assert "team-grid" in body
    assert "kpi-table" in body
    # The prototype's stage is gone.
    assert "dean-node" not in body, "the Dean node stage still renders"
    assert "priority-map" not in body, "the prototype's priority map still renders"


def test_the_stat_band_reports_the_portfolio(logged_in):
    body = _home(logged_in)
    for label in ("Initiatives", "Priorities", "Teams", "Team KPIs", "Need review"):
        assert label in body, "missing stat %s" % label


# --- every field the prototype carries --------------------------------------


def test_all_six_priorities_render(logged_in):
    from app import queries
    body = _home(logged_in)
    assert body.count('class="priority-card"') == 6
    for p in queries.blueprint_priorities():
        assert p["Title"] in body


def test_priority_cards_carry_the_governed_fields(logged_in):
    """Measure, target, cadence and owner - the four we did not hold before."""
    body = _home(logged_in)
    for label in ("Measure", "Target", "Cadence", "Owner"):
        assert label in body, "priority card missing %s" % label


def test_a_priorities_measure_target_and_cadence_actually_render(logged_in):
    """Not just the label: the prototype's own values."""
    from app import queries
    body = _home(logged_in)
    p = next(x for x in queries.blueprint_priorities() if x["Code"] == "P01")
    assert p["Measure"] in body
    assert p["Target"][:40] in body
    assert p["Cadence"] in body


def test_the_four_teams_render_with_descriptions(logged_in):
    body = _home(logged_in)
    assert body.count('class="team-card"') == 4
    for team in ("Learning Experiences", "Learning Ecosystems",
                 "Learning Infrastructure", "Learning Futures"):
        assert team in body


def test_all_29_team_kpis_render_with_their_fields(logged_in):
    from app import queries
    body = _home(logged_in)
    rows = queries.kpi_cards()
    assert len(rows) == 29
    assert body.count('class="kpi-row"') == 29
    # The table's columns cover the prototype's fields.
    for col in ("Code", "Team KPI", "Team", "Source area", "Strategy alignment",
                "Initiatives", "Target", "Target status", "Feeds"):
        assert col in body, "missing column %s" % col


def test_a_team_kpi_shows_its_team_source_area_and_priorities(logged_in):
    from app import queries
    body = _home(logged_in)
    k = queries.kpi_cards()[0]
    assert k["Team"] in body
    assert k["SourceArea"] in body
    # Its priority codes appear as chips.
    for p in k["priorities"]:
        assert p["Code"] in body


def test_the_needs_review_marker_is_shown(logged_in):
    from app import queries
    body = _home(logged_in)
    needs = [k for k in queries.kpi_cards() if k["TargetStatus"] == "needs_review"]
    assert needs, "expected some KPIs needing review"
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
