"""Group 6 of blueprint-redesign: verification.

The checks that must hold regardless of which design is in place: the token
discipline, print hygiene, keyboard reachability of the interactive pieces, and
that the superseded change is recorded.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")
PRINT_CSS = os.path.join(APP, "app", "static", "print.css")
BASE = os.path.join(APP, "app", "templates", "base.html")


def _sheet():
    return open(CSS, encoding="utf-8").read()


# --- 6.1 visual: tokens and no horizontal overflow --------------------------


def test_no_colour_literal_outside_a_token_block():
    """The token discipline survives the redesign."""
    from test_design_system import _outside_tokens
    outside = _outside_tokens(_sheet())
    offenders = [l.strip() for l in outside.split("\n")
                 if re.search(r"#[0-9a-fA-F]{3,8}\b", l.split("/*")[0])]
    assert not offenders, "literal colour outside tokens:\n" + "\n".join(offenders)


def test_horizontal_overflow_is_guarded():
    assert "overflow-x: hidden" in _sheet()


def test_both_palettes_render():
    """Dark chrome tokens and light content tokens both present."""
    css = _sheet()
    assert "--surface:" in css and "--accent:" in css
    assert "prefers-color-scheme: dark" in css


def test_the_responsive_breakpoints_exist():
    css = _sheet()
    assert "@media (max-width: 640px)" in css
    assert "@media (max-width: 900px)" in css or "@media (max-width: 1024px)" in css


# --- 6.2 keyboard ------------------------------------------------------------


def test_focus_visible_ring_is_defined():
    assert ":focus-visible" in _sheet()


def test_the_drawer_traps_and_restores_focus():
    base = open(BASE, encoding="utf-8").read()
    assert "keydown" in base and "Tab" in base
    assert "opener" in base and "opener.focus()" in base
    assert 'addEventListener("close"' in base


def test_the_nav_collapse_is_keyboard_operable():
    """A checkbox and label, so it needs no JavaScript and is reachable."""
    base = open(BASE, encoding="utf-8").read()
    assert 'id="nav-toggle"' in base
    assert 'for="nav-toggle"' in base


def test_the_user_menu_is_a_details_element():
    """<details>/<summary> is keyboard-operable by default."""
    base = open(BASE, encoding="utf-8").read()
    assert "<details" in base and "<summary" in base


def test_filter_controls_are_native():
    """The index filters use select/checkbox/button, all keyboard-native."""
    body = open(os.path.join(APP, "app", "templates", "initiatives.html"),
                encoding="utf-8").read()
    assert "<select" in body
    assert 'type="checkbox"' in body
    assert "<button" in body


# --- 6.3 print ---------------------------------------------------------------


def test_the_nav_is_hidden_for_print():
    both = _sheet() + open(PRINT_CSS, encoding="utf-8").read()
    assert ".site-nav" in both
    # A print rule hides the nav.
    assert re.search(r"@media print[^}]*\.site-nav", both, re.S) or \
           ".site-nav" in open(PRINT_CSS, encoding="utf-8").read()


def test_the_banner_is_hidden_for_print():
    assert re.search(r"@media print[^}]*sample-banner", _sheet(), re.S)


def test_print_css_exists_and_targets_chrome():
    assert os.path.exists(PRINT_CSS)
    t = open(PRINT_CSS, encoding="utf-8").read()
    assert ".site-header" in t and ".site-nav" in t


# --- 6.5 the superseded change is recorded ----------------------------------


def test_the_superseded_change_records_its_supersession():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(APP))),
                     "openspec", "changes", "overhaul-ui-ux-navigation", "tasks.md")
    t = open(p, encoding="utf-8").read()
    assert "SUPERSEDED" in t
    assert "blueprint-redesign" in t


def test_the_scope_correction_is_recorded():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(APP))),
                     "openspec", "changes", "blueprint-redesign", "proposal.md")
    t = open(p, encoding="utf-8").read()
    assert "SCOPE CORRECTION" in t
    # And it names the config contradiction it creates.
    assert "Nothing below D-1" in t
