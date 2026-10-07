"""Group 1 of blueprint-redesign: the visual system.

Covers the pieces the design-system tests in the superseded change did not: the
per-priority colour scale, the serif/sans split, and the guarantee that the two
colour scales never collapse into one another.
"""
import os
import re

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")
SCHEMA = os.path.join(APP, "db", "schema.sql")


def _sheet():
    return open(CSS, encoding="utf-8").read()


def _root():
    from test_design_system import _block_after
    return _block_after(_sheet(), ":root {")


# --- 1.1 the priority colour scale -----------------------------------------


def test_six_priority_colour_tokens_exist():
    """One key colour per priority code."""
    root = _root()
    for n in range(1, 7):
        assert ("--priority-%d:" % n) in root, "missing --priority-%d" % n


def test_priority_tokens_are_distinct():
    """Two priorities sharing a colour would defeat colour-as-key."""
    css = _sheet()
    values = []
    for n in range(1, 7):
        m = re.search(r"--priority-%d:\s*([^;]+);" % n, css)
        assert m, "no value for --priority-%d" % n
        values.append(m.group(1).strip())
    assert len(set(values)) == 6, "priority colours are not distinct: %s" % values


def test_every_priority_token_is_overridden_in_dark_mode():
    from test_design_system import _block_after
    dark = _block_after(_sheet(), "prefers-color-scheme: dark")
    for n in range(1, 7):
        assert ("--priority-%d:" % n) in dark, (
            "--priority-%d has no dark override, so it would be unreadable" % n)


# --- 1.3 the module that owns the scale -------------------------------------


def test_priority_codes_map_to_the_six_tokens():
    from app import status
    codes = ["P01", "P02", "P03", "P04", "P05", "P06"]
    tokens = [status.priority_colour_token(c) for c in codes]
    assert tokens == ["--priority-%d" % n for n in range(1, 7)]


def test_priority_colour_var_wraps_in_var():
    from app import status
    assert status.priority_colour_var("P03") == "var(--priority-3)"


def test_an_unknown_priority_still_gets_a_colour():
    """A new priority renders in a defined colour, not unstyled."""
    from app import status
    assert status.priority_colour_token("P99") == "--priority-1"
    assert status.priority_colour_token("") == "--priority-1"


# --- the two scales must not collapse ---------------------------------------


def test_the_priority_scale_does_not_invent_a_status():
    """The status vocabulary is still exactly the schema's."""
    from app import status
    schema = open(SCHEMA, encoding="utf-8").read()
    # Scope to the initiative table (ADR-0002: three vocabularies exist).
    block = schema.split("CREATE TABLE TeamInitiativeUpdates")[1].split(");")[0]
    m = re.search(r"CHECK\s*\(\s*Status\s+IN\s*\(([^)]*)\)", block)
    assert m, "no initiative Status CHECK in the schema"
    from_schema = [v.strip().strip("'") for v in m.group(1).split(",") if v.strip()]
    assert list(status.vocabulary()) == from_schema


def test_priority_colour_is_not_a_status_colour():
    """No priority colour is one of the status colours.

    If they overlapped, a reader could not tell which scale a colour belonged
    to - the exact confusion the separate scales exist to prevent.
    """
    css = _sheet()
    status_values = set()
    for name in ("on-track", "at-risk", "off-track", "not-started",
                 "paused", "complete"):
        m = re.search(r"--status-%s:\s*([^;]+);" % name, css)
        if m and not m.group(1).strip().startswith("var("):
            status_values.add(m.group(1).strip().lower())
    priority_values = set()
    for n in range(1, 7):
        m = re.search(r"--priority-%d:\s*([^;]+);" % n, css)
        priority_values.add(m.group(1).strip().lower())
    overlap = status_values & priority_values
    assert not overlap, "a priority colour equals a status colour: %s" % overlap


# --- 1.2 the display / sans / serif split -----------------------------------


def test_font_family_tokens_exist():
    root = _root()
    assert "--font-display" in root, "no display family token"
    assert "--font-serif" in root, "no serif family token"
    assert "--font-sans" in root, "no sans family token"


def test_headings_use_the_display_token():
    """Headings use the display face. Hive's display is Barlow, a sans display
    face, so this replaced the earlier serif-heading check (the restyle brief,
    section 8). --font-serif stays for ledes and reading text."""
    css = _sheet()
    for sel in ("h1", "h2"):
        m = re.search(r"(?m)^%s \{([^}]*)\}" % sel, css)
        assert m, "no %s rule" % sel
        assert "var(--font-display)" in m.group(1), "%s is not the display face" % sel


def test_body_uses_the_sans_token():
    css = _sheet()
    m = re.search(r"body \{([^}]*)\}", css, re.S)
    assert m and "var(--font-sans)" in m.group(1), "body is not sans"


# --- the section-heading pattern --------------------------------------------


def test_section_heading_pattern_is_defined():
    """eyebrow -> serif heading -> note, the de-flattening pattern."""
    css = _sheet()
    for cls in (".eyebrow", ".section-heading", ".section-note"):
        assert cls in css, "no %s rule" % cls


# --- 1.4 components carried over, and the token discipline ------------------


def test_no_colour_literal_outside_a_token_block():
    """The priority scale must not have introduced a literal."""
    from test_design_system import _outside_tokens
    outside = _outside_tokens(_sheet())
    offenders = []
    for i, line in enumerate(outside.split("\n"), 1):
        code = line.split("/*")[0]
        if re.search(r"#[0-9a-fA-F]{3,8}\b", code) or re.search(r"\brgba?\(", code):
            offenders.append("line %d: %s" % (i, line.strip()))
    assert not offenders, "literal colour outside tokens:\n" + "\n".join(offenders)


def test_priority_filter_is_registered(logged_in):
    """The filter is on the render path, so a card can use it."""
    from app.main import templates
    assert "priority_colour" in templates.env.filters
    # And it renders a var() for a real code.
    from app import status
    assert status.priority_colour_var("P01").startswith("var(--")


def test_priority_chips_render_a_colour_token_not_a_double_var(logged_in):
    """The chips' inline colour must be valid CSS.

    The defect (found 2026-10-07): the chips asked for a priority's DB hex and
    passed it to the var()-returning filter, then wrapped it in var() again -
    `var(var(--priority-1))`, which is invalid, so every priority chip rendered
    uncoloured. They now ask by code for the TOKEN and wrap it once, like the
    home card.
    """
    body = logged_in("Bill Gaudelli").get("/team-initiatives").text
    assert "var(var(" not in body, "a double var() survives - the chip colour is invalid"
    tokens = set(re.findall(r"--priority: var\((--priority-\d)\)", body))
    assert len(tokens) >= 2, "the chips render no priority colour tokens: %s" % tokens
    assert all(t.startswith("--priority-") for t in tokens)
