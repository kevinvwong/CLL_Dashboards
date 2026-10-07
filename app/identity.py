"""Identity for goals and teams: a colour token and an icon, keyed by id.

The app has four independent identity axes (ADR-0003): priority (its own six
colours), status (the semantic traffic-light), goal (five) and team (four).
Each is a code->token map here, never a database column, so a colour re-maps for
the dark palette in CSS instead of being frozen as a hex.

Priority identity already lives in `status.py` (PRIORITY_COLOUR_TOKENS), beside
the status scale it must not be confused with. Goal and team identity live here,
for the same reason: one place that knows how an id maps to a colour and a mark.
"""

#: goal number (1..5) -> CSS custom property name.
GOAL_COLOUR_TOKENS = {
    1: "--goal-1",
    2: "--goal-2",
    3: "--goal-3",
    4: "--goal-4",
    5: "--goal-5",
}

#: team id -> CSS custom property name.
TEAM_COLOUR_TOKENS = {
    1: "--team-1",
    2: "--team-2",
    3: "--team-3",
    4: "--team-4",
}

#: goal number -> the inner markup of a 24x24 stroke icon. Stroke-based and
#: currentColor, so an icon takes its goal's colour and survives greyscale. These
#: are simple geometric marks, not a pictorial set: the goal's NAME is always
#: beside the icon, so the icon is a recognisable anchor, never the only signal.
_GOAL_ICONS = {
    1: ('<path d="M4 5h7v14H4z"/><path d="M13 5h7v14h-7z"/>'),  # open book
    2: ('<circle cx="12" cy="12" r="8"/>'
        '<path d="M4 12h16"/>'
        '<path d="M12 4c2.8 2.8 2.8 12.4 0 16"/>'
        '<path d="M12 4c-2.8 2.8-2.8 12.4 0 16"/>'),  # globe
    3: ('<circle cx="12" cy="8" r="3.2"/>'
        '<path d="M5.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'),  # person
    4: ('<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>'),  # magnifier
    5: ('<circle cx="12" cy="12" r="3.2"/>'
        '<path d="M12 3v3M12 18v3M3 12h3M18 12h3"/>'
        '<path d="M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1"/>'
        '<path d="M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>'),  # gear
}


def goal_colour_token(goal_number) -> str:
    """The CSS custom property holding a goal's key colour."""
    try:
        number = int(goal_number)
    except (TypeError, ValueError):
        return "--goal-1"
    return GOAL_COLOUR_TOKENS.get(number, "--goal-1")


def team_colour_token(team_id) -> str:
    """The CSS custom property holding a team's key colour."""
    try:
        tid = int(team_id)
    except (TypeError, ValueError):
        return "--team-1"
    return TEAM_COLOUR_TOKENS.get(tid, "--team-1")


def goal_icon(goal_number) -> str:
    """The inline SVG for a goal, coloured by currentColor, hidden from a reader.

    The goal's name is always rendered beside the icon, so it is decorative:
    aria-hidden and focusable=false, and it carries no text a screen reader
    needs.
    """
    try:
        number = int(goal_number)
    except (TypeError, ValueError):
        number = 1
    body = _GOAL_ICONS.get(number, _GOAL_ICONS[1])
    return ('<svg class="goal-icon" viewBox="0 0 24 24" width="18" height="18" '
            'fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>' % body)
