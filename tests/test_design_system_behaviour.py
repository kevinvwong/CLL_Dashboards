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

# test_the_bar_is_at_most_32px: retired 2026-10-07 - the sample-data banner was removed
# when the register was approved.

def test_the_three_breakpoints_are_defined():
    """Mobile ≤767, tablet 768-1024, desktop ≥1025 (app-shell, 2026-10-07)."""
    css = _sheet()
    assert "@media (max-width: 767px)" in css
    assert "@media (min-width: 768px) and (max-width: 1024px)" in css
    assert "@media (min-width: 1025px)" in css


def test_no_horizontal_overflow_guard():
    css = _sheet()
    assert "overflow-x: hidden" in css


def test_the_nav_is_a_rail_and_a_tab_bar_not_a_checkbox():
    """Supersedes the checkbox-collapse nav: the shell is a grid rail plus a
    mobile tab bar (app-shell, 2026-10-07). The rail and tab bar render only for
    a signed-in person (pre-auth pages are chrome-free)."""
    base = _base()
    assert "app-shell" in base, "the app-shell host is missing"
    assert "site-nav" in base, "the rail is missing"
    assert "tabbar" in base, "the mobile tab bar is missing"
    assert "app-shell--bare" in base, "the pre-auth bare-shell variant is missing"
    css = _sheet()
    assert ".nav-toggle" not in css, "the retired checkbox nav is still styled"


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
