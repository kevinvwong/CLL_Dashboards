"""The shared card component (card unification, 2026-10-08).

One card family composed by every card page: the goal, team, lens, initiative
and priority cards share `.card` plus its parts. The per-page names
(.goal-card, .team-card, ...) survive as aliases, so a page adopting the
component does not change what a reader sees.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")


def _sheet():
    return open(CSS, encoding="utf-8").read()


def test_the_shared_card_parts_are_defined_once():
    css = _sheet()
    for part in (".card {", ".card-head", ".card-id", ".card-title", ".card-sub",
                 ".card-count", ".card-bar", ".card-fill", ".card-link"):
        assert part in css, "the shared card component is missing %s" % part
    # One base definition, not two competing ones.
    assert css.count(".card {") == 1, "there is more than one .card base rule"


def test_the_old_per_page_names_are_aliased_not_removed():
    """The pinned class names survive, so nothing that renders them changes."""
    css = _sheet()
    for old in (".goal-card", ".priority-card", ".team-card", ".person-card",
                ".lens-card", ".oct16-card"):
        assert old in css, "%s was removed rather than aliased" % old


def test_the_auth_card_does_not_cap_the_shared_component():
    """The login/whoami `.card` had a max-width; scoped so it cannot cap the
    shared component's cards."""
    css = _sheet()
    assert ".card.login, .card.whoami" in css


def test_goal_and_team_cards_carry_a_status_mix(logged_in):
    goals = logged_in("Bill Gaudelli").get("/goals").text
    assert goals.count("card-mix") >= 5, "goal cards have no status mix"
    teams = logged_in("Bill Gaudelli").get("/teams").text
    assert teams.count("card-mix") >= 4, "team cards have no status mix"


def test_the_landing_hero_and_lens_cards_use_the_component(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'class="oct16-card card ' in body or "oct16-card card" in body
    assert "lens-card card" in body
    assert "card-link" in body
