"""Group 6 of blueprint-redesign: verification.

The checks that must hold regardless of which design is in place: the token
discipline, print hygiene, and keyboard reachability of the interactive pieces.

The two tests that used to live here asserted on OpenSpec artifacts (the
superseded change's `tasks.md`, and the archived proposal's "SCOPE CORRECTION").
OpenSpec was removed on 2026-10-06, so their subject no longer exists. The
decisions they guarded are recorded in the design docs under
`docs/superpowers/specs/`: the supersession of `overhaul-ui-ux-navigation` in
`2026-10-06-blueprint-redesign-design.md`, and the `config.yaml` contradiction
in `2026-10-06-interconnection-redesign-design.md`.
"""
import os
import re
import sys

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


def test_the_nav_is_reachable_and_has_a_skip_link():
    """The rail is a real nav; a skip link past it is the app-shell contract
    (supersedes the checkbox-collapse test, 2026-10-07)."""
    base = open(BASE, encoding="utf-8").read()
    assert 'aria-label="Primary"' in base
    assert 'class="skip-link"' in base
    assert 'href="#content"' in base
    assert 'id="content"' in base


def test_the_user_menu_is_a_details_element():
    """<details>/<summary> is keyboard-operable by default."""
    base = open(BASE, encoding="utf-8").read()
    assert "<details" in base and "<summary" in base


def test_filter_controls_are_native():
    """The index filter controls are keyboard-native.

    Read from the LIVE partial (_mi_table.html), not from the superseded
    initiatives.html. No route renders that template and its filter controls are
    unreachable, so asserting on it would test dead markup - and would keep
    passing even if the live filter were broken."""
    body = open(os.path.join(APP, "app", "templates", "_mi_table.html"),
                encoding="utf-8").read()
    assert 'class="chip' in body        # filter / group chips
    assert "<nav" in body               # the controls are a landmark
    assert "<a " in body                # links, so they work before hydration


# --- 6.3 print ---------------------------------------------------------------


def test_the_nav_is_hidden_for_print():
    both = _sheet() + open(PRINT_CSS, encoding="utf-8").read()
    assert ".site-nav" in both
    # A print rule hides the nav.
    assert re.search(r"@media print[^}]*\.site-nav", both, re.S) or \
           ".site-nav" in open(PRINT_CSS, encoding="utf-8").read()


# test_the_banner_is_hidden_for_print: retired 2026-10-07 - the sample-data banner was removed
# when the register was approved.

def test_print_css_exists_and_targets_chrome():
    assert os.path.exists(PRINT_CSS)
    t = open(PRINT_CSS, encoding="utf-8").read()
    assert ".site-header" in t and ".site-nav" in t


# --- the authoritative meeting record stays out of the app -------------------
#
# docs/record/ holds the Dean+COO meeting record. It is a repository audit
# artefact, not content: it names participants, discusses capacity concerns and
# contains unreleased plans. `app/docs.py` renders ONLY files listed in
# docs/guide.yaml, so the guarantee is the absence of a manifest entry - this
# test holds that line, because "we forgot to add it" is the exact way it would
# be breached.


def test_the_meeting_record_is_not_in_the_in_app_guide():
    manifest = open(os.path.join(APP, "docs", "guide.yaml"), encoding="utf-8").read()
    assert not re.search(r"path:\s*(record|plan)/", manifest), (
        "docs/record or docs/plan is listed in guide.yaml, so the meeting "
        "record would be served inside the app")


def test_the_meeting_record_transcription_is_current():
    """The .md is generated; --check proves it still matches the .docx."""
    import subprocess
    root = APP
    r = subprocess.run(
        [sys.executable, os.path.join(root, "scripts", "transcribe_record.py"), "--check"],
        capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, (r.stdout + r.stderr).strip()
