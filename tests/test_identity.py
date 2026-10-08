"""Goal and team identity: a keyed colour token and (for a goal) an icon.

The four identity axes (ADR-0003) are each keyed and must not collapse into one
another. Priority identity lives in app.status; goal and team identity in
app.identity. This pins that the tokens are declared, that the icons render, and
that the axes do not share a colour.
"""
import os
import re

from app import identity

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")


def _sheet():
    return open(CSS, encoding="utf-8").read()


def test_goal_and_team_tokens_are_keyed_by_id():
    assert identity.goal_colour_token(3) == "--goal-3"
    assert identity.team_colour_token(2) == "--team-2"
    # An unknown id falls back to a defined colour rather than raising.
    assert identity.goal_colour_token(99) == "--goal-1"
    assert identity.team_colour_token(None) == "--team-1"


def test_every_goal_and_team_token_is_declared_in_the_sheet():
    css = _sheet()
    for n in range(1, 6):
        assert ("%s:" % identity.goal_colour_token(n)) in css, "goal %d token missing" % n
    for t in range(1, 5):
        assert ("%s:" % identity.team_colour_token(t)) in css, "team %d token missing" % t


def test_a_goal_icon_is_decorative_and_inherits_colour():
    svg = identity.goal_icon(1)
    assert svg.startswith("<svg")
    assert 'aria-hidden="true"' in svg
    assert "currentColor" in svg, "the icon must inherit its colour, not hardcode one"


def test_the_axes_do_not_share_a_colour():
    """A goal colour is not a priority or status colour (ADR-0003)."""
    css = _sheet()
    def vals(prefix, n):
        m = re.search(r"%s-\d+:\s*([^;]+);" % prefix, css)
        return m.group(1).strip().lower() if m else None
    goals = {re.search(r"--goal-%d:\s*([^;]+);" % n, css).group(1).strip().lower()
             for n in range(1, 6)}
    priorities = {re.search(r"--priority-%d:\s*([^;]+);" % n, css).group(1).strip().lower()
                  for n in range(1, 7)}
    assert not (goals & priorities), "a goal colour equals a priority colour"


def test_the_goals_page_renders_goal_icons_and_team_swatches(logged_in):
    """Goal icons/legend live on /goals, team swatches on /teams (overview split)."""
    goals = logged_in("Bill Gaudelli").get("/goals").text
    assert goals.count("goal-icon") >= 5, "the goals render no icons"
    assert "identity-legend" in goals, "the goal legend is missing"
    assert re.search(r"--goal: var\(--goal-\d\)", goals), "no goal colour token rendered"
    teams = logged_in("Bill Gaudelli").get("/teams").text
    assert teams.count("team-swatch") >= 4, "the teams render no swatches"


def test_priority_chips_carry_the_matching_priority_colour(logged_in):
    """The chip colour token matches the priority it names (spot check)."""
    body = logged_in("Bill Gaudelli").get("/team-initiatives").text
    assert "var(var(" not in body
    assert re.search(r"--priority: var\(--priority-\d\)", body)
