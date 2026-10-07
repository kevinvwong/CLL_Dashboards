"""The six annual priorities, canonically named.

Provenance: the Dean's prototype (`cll-blueprint-2027.wag32002.chatgpt.site`,
`data.js`), which `deans-prototype-reading.md` records as agreeing word for
word with the PMO workbook and the wireframes' Option A. The database stores
only the short name and plan year, so the code, the full title and the
description live here, read by the blueprint home.

This is a NAME-to-canonical map, not a second source of truth for what exists:
the database still decides which priorities there are. A priority the database
holds but this map does not simply renders with its short name and no code.
"""

# short database name -> (code, full title, description)
PRIORITIES = {
    "Identity": (
        "P01",
        "One Shared Identity",
        "Build a clear, cohesive sense of who we are as a College and "
        "consistently communicate the distinctive value of CLL.",
    ),
    "Innovation": (
        "P02",
        "Champion Innovation",
        "Foster experimentation, creativity, and new ways of working that "
        "advance learning, improve outcomes, and position CLL for the future.",
    ),
    "Pathways": (
        "P03",
        "Integrated Portfolio & Pathways",
        "Connect programs, credentials, and learning experiences into clear, "
        "cohesive pathways that help learners navigate opportunities and "
        "achieve their goals.",
    ),
    "Scale": (
        "P04",
        "Quality at Scale",
        "Deliver consistent, high-quality experiences and outcomes as we "
        "expand our reach, programs, and impact.",
    ),
    "Data": (
        "P05",
        "Data-Informed Action",
        "Use data and insights to inform decisions, prioritize action, "
        "measure impact, and continuously improve.",
    ),
    "Culture": (
        "P06",
        "Culture & Learning",
        "Strengthen a culture of continuous learning, collaboration, and "
        "shared accountability that brings our modeled behaviors to life and "
        "builds the capabilities needed for CLL\u2019s future.",
    ),
}


def code(name: str) -> str:
    """The priority code, or "" if the name is not one of the six canonical."""
    entry = PRIORITIES.get((name or "").strip())
    return entry[0] if entry else ""


def title(name: str) -> str:
    """The full title, falling back to the short name the database holds."""
    entry = PRIORITIES.get((name or "").strip())
    return entry[1] if entry else (name or "")


def description(name: str) -> str:
    """The canonical description, or "" when not one of the six."""
    entry = PRIORITIES.get((name or "").strip())
    return entry[2] if entry else ""


def label(name: str) -> str:
    """The ONE label a priority is called by, everywhere.

    "Priority 1 · One Shared Identity" - the word, the number, then the title.
    It read "P01 One Shared Identity" (a code glued to a name) and, before that,
    three different ways. "P01" is the database code and stays as the key; on
    screen it is spelled out (design review, 2026-10-07). A priority whose name is
    not one of the six, or one with no code, falls back to the database's name.
    """
    c = code(name)
    t = title(name)
    if not c:
        return t
    number = str(int(c[1:])) if c[1:].isdigit() else c  # 'P01' -> '1'
    return "Priority %s · %s" % (number, t)


def number(name: str) -> str:
    """A priority's number as a word-phrase: 'Priority 1'. "" for a non-priority."""
    c = code(name)
    if not c:
        return ""
    n = str(int(c[1:])) if c[1:].isdigit() else c
    return "Priority %s" % n


#: Register the template filters, so a template can write `| priority_label`.
FILTERS = {"code": code, "title": title, "description": description, "label": label}
