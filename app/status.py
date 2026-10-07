"""Status presentation: one vocabulary, one slug, one colour.

Design D4 of deepen-dashboard-modules. The status vocabulary has one source of
truth - the schema's own CHECK constraint - and one place it is turned into a
CSS class. Templates call this module and never transform a status themselves.

Why this exists: the same status was slugged in six templates with
`| lower | replace(' ', '-')`, and the colours were defined only as
`.bar-fill.status-*`, so a status badge outside a bar rendered uncoloured, and
the oct16 milestone classes `m-*` had no rule at all. One module removes the
six copies and makes "every emitted class has a style" checkable.
"""

import os
import re

_SCHEMA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))),
    "db", "schema.sql",
)

# The vocabulary, if the schema cannot be read. The test asserts these equal the
# schema's CHECK values, so a drift fails a test rather than rendering silently.
_FALLBACK = ("Not started", "On track", "At risk", "Off track", "Complete", "Paused")


def vocabulary() -> tuple:
    """The status values the schema allows.

    Read from the schema's `CHECK (Status IN (...))`, so the schema remains the
    source of truth and this module cannot invent a status the database would
    refuse.
    """
    try:
        text = open(_SCHEMA, encoding="utf-8").read()
    except OSError:
        return _FALLBACK
    m = re.search(r"CHECK\s*\(\s*Status\s+IN\s*\(([^)]*)\)", text)
    if not m:
        return _FALLBACK
    return tuple(v.strip().strip("'") for v in m.group(1).split(",") if v.strip())


def slug(value: str) -> str:
    """A status as a CSS class fragment: "At risk" -> "at-risk".

    The one transform. Every template that shows a status calls this instead of
    re-implementing `| lower | replace(' ', '-')`.
    """
    return re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")


def status_class(value: str) -> str:
    """The class for an initiative status, e.g. "status-at-risk".

    Used for a bar fill AND a standalone badge, so the colour follows the status
    wherever it is shown.
    """
    return "status-" + slug(value)


#: A glyph per status, so status is not carried by colour alone (WCAG 1.4.1).
#: A shape + colour + the word itself survives colourblindness, greyscale print
#: and a forced-colours mode. Chosen to read at small sizes: a filled/hollow
#: circle, a triangle for risk, a square for a hard stop, a tick for complete.
_STATUS_ICON = {
    "not started": "\u25cb",   # ○ hollow circle
    "on track": "\u25cf",      # ● filled circle
    "at risk": "\u25b2",       # ▲ triangle
    "off track": "\u25a0",     # ■ square
    "complete": "\u2713",      # ✓ tick
    "paused": "\u2016",        # ‖ pause bars
}


def status_icon(value: str) -> str:
    """The glyph for a status, or "" for one not in the vocabulary.

    The glyph is decoration; the status word is always rendered beside it, so a
    screen reader still hears the status text. Empty in, empty out.
    """
    return _STATUS_ICON.get((value or "").strip().lower(), "")


def milestone_class(value: str) -> str:
    """The class for a milestone status, e.g. "m-in-progress"."""
    return "m-" + slug(value)


def availability_class(value: str) -> str:
    """The class for a data-requirements availability cell."""
    return "availability-" + slug(value)


# --- the per-priority colour scale (blueprint-redesign task 1.3) -------------
#
# Six key colours, each tied to its priority CODE (P01-P06), adopted from the
# Dean's prototype's own PRIORITIES data. These are NOT status colours and must
# never be used as one: the status scale is read from the schema above. A
# priority keeps its colour wherever it appears, so a reader can track a
# priority across the stage, the cards and the cascade by colour alone.

#: code -> CSS custom property name. Kept beside the module's other mappings so
#: there is one place that knows how a priority maps to a colour.
PRIORITY_COLOUR_TOKENS = {
    "P01": "--priority-1",
    "P02": "--priority-2",
    "P03": "--priority-3",
    "P04": "--priority-4",
    "P05": "--priority-5",
    "P06": "--priority-6",
}


def priority_colour_token(code: str) -> str:
    """The CSS custom property holding a priority's key colour.

    Unknown codes fall back to the first token rather than raising, so a new
    priority renders in a defined colour instead of an unstyled one.
    """
    return PRIORITY_COLOUR_TOKENS.get((code or "").strip().upper(),
                                      "--priority-1")


def priority_colour_var(code: str) -> str:
    """The `var(...)` expression for a priority's colour.

    For inline styles, where a class cannot carry the value.
    """
    return "var(%s)" % priority_colour_token(code)

