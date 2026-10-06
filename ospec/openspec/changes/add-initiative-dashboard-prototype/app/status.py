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


def milestone_class(value: str) -> str:
    """The class for a milestone status, e.g. "m-in-progress"."""
    return "m-" + slug(value)


def availability_class(value: str) -> str:
    """The class for a data-requirements availability cell."""
    return "availability-" + slug(value)
