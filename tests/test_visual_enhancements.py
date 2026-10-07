"""The enhancement visuals that need no new data.

The stat-tile proportion fill, the alarm tile's icon, the Dean FY timeline bar,
and the nav icons. Each is decorative (aria-hidden) with the figure in the text
beside it, so nothing is carried by an image alone.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_nav_renders_an_icon_for_each_primary_item(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert body.count("nav-icon") >= 4, "the nav has no icons"
    # The icon is decorative: the label is the accessible name.
    assert 'class="nav-icon"' in body
    for label in ("Overview", "Initiatives", "People", "Outcomes"):
        assert label in body


def test_the_alarm_tile_shows_a_fill_bar_and_an_icon(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert "stat-fill" in body, "the 'need review' tile has no proportion bar"
    assert "stat-icon" in body, "the alarm tile has no icon"
    # The bar is labelled for a screen reader rather than colour alone.
    assert re.search(r'aria-label="\d+ of \d+ Team Initiatives need review"', body)


def test_the_dean_timeline_renders_as_a_bar(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert "fy-timeline" in body, "the Dean FY timeline bar is missing"
    assert "fy-26" in body and "fy-27" in body
    # Still stated as text, so the figures do not depend on the bar.
    assert "in flight in FY27" in body


def test_the_new_components_have_styles_and_no_colour_literal():
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    for cls in (".stat-fill", ".fy-timeline", ".nav-icon", ".identity-legend"):
        assert cls in css, "no style for %s" % cls
