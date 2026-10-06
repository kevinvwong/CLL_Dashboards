"""The design system: token discipline, components, and the schema status set.

Covers tasks 2.1-2.3 of overhaul-ui-ux-navigation.

The token check is the load-bearing one: it scans the shipped stylesheet and
fails if a colour literal appears outside a token block, so a literal cannot
creep back in page by page as the rest of the change migrates templates.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(APP, "app", "static", "style.css")
SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(APP))),
                      "db", "schema.sql")


def _sheet():
    return open(CSS, encoding="utf-8").read()


def _token_blocks(text):
    """Line ranges that hold token declarations (the :root block and its
    prefers-color-scheme override). Literal values are allowed there and
    nowhere else. Brace-matched, so a nested media query is not mistaken for
    the end of the block."""
    lines = text.split("\n")
    ranges = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == ":root {":
            depth = 0
            start = i
            for j in range(i, len(lines)):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    ranges.append((start, j))
                    i = j
                    break
        i += 1
    return ranges


def _strip_comments(text):
    """Blank out /* ... */ comments, preserving line numbers.

    Needed because the sheet's own prose names the patterns it forbids ("hex or
    rgb() value"), which would otherwise make the check flag its own
    documentation - and a gate that fires on correct input gets switched off.
    """
    lines = text.split("\n")
    in_comment = False
    out = []
    for line in lines:
        if in_comment:
            if "*/" in line:
                line = line.split("*/", 1)[1]
                in_comment = False
            else:
                out.append("")
                continue
        while "/*" in line:
            before, rest = line.split("/*", 1)
            if "*/" in rest:
                line = before + rest.split("*/", 1)[1]
            else:
                line = before
                in_comment = True
                break
        out.append(line)
    return "\n".join(out)


def _outside_tokens(text):
    """The sheet with token blocks and comments blanked, line numbers kept."""
    text = _strip_comments(text)
    lines = text.split("\n")
    for start, end in _token_blocks(text):
        for i in range(start, end + 1):
            lines[i] = ""
    return "\n".join(lines)


# --- 2.1 tokens -------------------------------------------------------------


def test_no_colour_literal_outside_a_token_block():
    """A colour literal outside :root means a page bypassed the design system."""
    outside = _outside_tokens(_sheet())
    offenders = []
    for i, line in enumerate(outside.split("\n"), 1):
        # Skip comments: this file's own prose names the pattern it forbids.
        code = line.split("/*")[0]
        if re.search(r"#[0-9a-fA-F]{3,8}\b", code) or re.search(r"\brgba?\(", code):
            offenders.append("line %d: %s" % (i, line.strip()))
    assert not offenders, (
        "colour literal(s) outside the token block; use a var(--token):\n"
        + "\n".join(offenders))


def test_colour_tokens_are_declared_and_used():
    """Every colour token is both declared and referenced."""
    t = _sheet()
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", t))
    used = set(re.findall(r"var\((--[a-z0-9-]+)\)", t))
    colourish = {d for d in declared if re.search(r"ink|surface|accent|line|error|warn|status|backdrop", d)}
    assert not (colourish - used), "declared colour tokens never used: %s" % sorted(colourish - used)
    assert not (used - declared), "used but undeclared: %s" % sorted(used - declared)


def test_spacing_radius_and_type_tokens_exist():
    t = _sheet()
    for name in ("--space-1", "--space-2", "--space-3", "--space-4",
                 "--radius-sm", "--radius-md", "--radius-lg",
                 "--text-xs", "--text-sm", "--text-base", "--text-lg",
                 "--shadow-sm", "--shadow-md"):
        assert ("%s:" % name) in t, "missing token %s" % name


def _block_after(text, opener):
    """The { ... } block whose opening line contains `opener`, brace-matched.

    A regex with a lazy `.*?` stops at the first `}` and mis-reads these nested
    blocks, which is exactly the kind of near-miss that makes a check look
    authoritative while measuring the wrong thing.
    """
    start = text.find(opener)
    if start == -1:
        return ""
    brace = text.find("{", start)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:i]
    return ""


def test_dark_mode_overrides_every_colour_token():
    """A dark theme that misses a token leaves that surface light."""
    t = _sheet()
    root = _block_after(t, ":root {")
    dark = _block_after(t, "prefers-color-scheme: dark")
    assert root and dark, "could not locate the token blocks"

    def names(block):
        return set(re.findall(r"(--[a-z0-9-]+)\s*:", block))

    root_colours = {n for n in names(root)
                    if re.search(r"ink|surface|accent|line|error|warn|status|backdrop", n)}
    dark_colours = names(dark)
    missing = root_colours - dark_colours
    assert not missing, "dark mode does not override: %s" % sorted(missing)


def test_no_font_size_literal_outside_tokens():
    """Type is on the scale, so headings and body do not drift by page."""
    outside = _outside_tokens(_sheet())
    offenders = [l.strip() for l in outside.split("\n")
                 if re.search(r"font-size:\s*[0-9.]+rem", l)]
    assert not offenders, "font-size literal outside tokens:\n" + "\n".join(offenders)


# --- 2.2 shared components --------------------------------------------------


def test_component_classes_are_defined():
    """Every component the spec names has at least one rule."""
    t = _sheet()
    for cls in (".card-modal", ".card-body", ".badge", ".bar", ".bar-fill",
                ".initiative-row", ".tile", ".button", ".error-page",
                ".breadcrumb", ".toast", ".drawer", ".empty", ".chip", ".field"):
        assert cls in t, "no CSS for component %r" % cls


def test_button_variants_exist():
    t = _sheet()
    for variant in (".button.primary", ".button.secondary", ".button.ghost"):
        assert variant in t, "no button variant %r" % variant


# --- 2.3 the status set is the schema's ------------------------------------


def test_status_classes_cover_exactly_the_schema_statuses():
    """The component's status set equals the schema's CHECK values.

    This is the design-system half of the `status-presentation` rule: one
    vocabulary, read from the database, not restated in the design.
    """
    schema = open(SCHEMA, encoding="utf-8").read()
    m = re.search(r"CHECK\s*\(\s*Status\s+IN\s*\(([^)]*)\)", schema)
    assert m, "no Status CHECK in the schema"
    schema_statuses = [v.strip().strip("'") for v in m.group(1).split(",") if v.strip()]

    from app import status
    assert list(status.vocabulary()) == schema_statuses, (
        "the status module and the schema disagree")

    # Every schema status produces a class that has a CSS rule.
    css = _sheet()
    for value in schema_statuses:
        cls = status.status_class(value)
        assert ("." + cls) in css, "no CSS rule for %r" % cls


def test_no_status_word_the_schema_cannot_store():
    """The design draft used "Done"; the schema cannot store it.

    Guards against the scale being restated from the design rather than read
    from the database.
    """
    from app import status
    assert "Done" not in status.vocabulary()
    # And the stylesheet does not invent one either.
    assert "status-done" not in _sheet()
