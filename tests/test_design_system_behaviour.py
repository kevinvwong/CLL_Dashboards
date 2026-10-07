"""Design-system behaviour: the banner, the responsive rules, focus handling.

Covers tasks 2.4-2.6 of overhaul-ui-ux-navigation. The token and component
checks live in test_design_system.py; these are the behavioural ones.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")
BASE = os.path.join(APP, "app", "templates", "base.html")


def _sheet():
    return open(CSS, encoding="utf-8").read()


def _base():
    return open(BASE, encoding="utf-8").read()


# --- 2.4 the sample-data bar and the persistent marker ---------------------


# test_one_banner_replaces_two: retired 2026-10-07 - the sample-data banner was removed when the
# register was approved, so this tests a deleted feature.

# test_the_bar_is_dismissible_for_the_session: retired 2026-10-07 - the sample-data banner was removed when the
# register was approved, so this tests a deleted feature.

# test_the_bar_shows_when_not_dismissed: retired 2026-10-07 - the sample-data banner was removed when the
# register was approved, so this tests a deleted feature.

# test_the_footer_marker_survives_dismissal: retired 2026-10-07 - the sample-data banner was removed when the
# register was approved, so this tests a deleted feature.

def test_the_bar_is_at_most_32px():
    """The spec caps it at 32px."""
    css = _sheet()
    rule = re.search(r"\.sample-banner\s*\{(.*?)\}", css, re.S)
    assert rule, "no .sample-banner rule"
    assert "max-height: var(--space-8)" in rule.group(1), (
        "the bar must cap at the 32px token")


# --- 2.5 responsive layout --------------------------------------------------


def test_the_three_breakpoints_are_defined():
    css = _sheet()
    assert "@media (max-width: 640px)" in css
    assert "@media (min-width: 641px) and (max-width: 1024px)" in css
    assert "@media (min-width: 1025px)" in css


def test_no_horizontal_overflow_guard():
    css = _sheet()
    assert "overflow-x: hidden" in css


def test_the_nav_collapses_without_javascript():
    """A checkbox toggle, so the nav works before hydration."""
    base = _base()
    assert 'class="nav-toggle"' in base
    assert 'class="nav-toggle-label"' in base
    css = _sheet()
    assert ".nav-toggle:checked ~ .site-nav" in css


# --- 2.6 focus and overlay behaviour ---------------------------------------


def test_focus_ring_is_defined_and_not_removed_without_replacement():
    css = _sheet()
    assert ":focus-visible" in css
    assert "outline: 2px solid var(--accent)" in css


def test_modal_traps_focus_and_returns_it():
    base = _base()
    # Tab is intercepted inside the modal...
    assert "keydown" in base and "Tab" in base
    # ...the opener is remembered and refocused on close.
    assert "opener" in base
    assert 'addEventListener("close"' in base
    assert "opener.focus()" in base


def test_page_scroll_is_locked_while_an_overlay_is_open():
    base = _base()
    assert "overlay-open" in base
    assert "overflow: hidden" in _sheet()
