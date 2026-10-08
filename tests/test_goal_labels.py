"""Review round (2026-10-07): goal labels and the list eyebrow.

"G1" was the abbreviation everywhere, including in the list eyebrow where it
read "Goal G1" - a label glued to its own abbreviation. The register writes
"Goal 1", so the app spells it out in prose and keeps the short "G1" only in the
compact Team Initiatives table, where five goals share a cell.
"""


def test_home_goal_tiles_spell_out_goal(logged_in):
    """The goal tiles moved to /goals (overview split, 2026-10-07)."""
    body = logged_in("Bill Gaudelli").get("/goals").text
    assert "Goal 1" in body or "Goal 2" in body, "goal tiles still abbreviate to G1"
    # the bare chip form should not appear on the goal tiles
    assert 'class="goal-number">G1<' not in body


def test_team_initiative_goal_chip_spells_it_out(logged_in):
    body = logged_in("Bill Gaudelli").get("/team-initiatives/MI-001").text
    assert "Goal 1" in body or "Goal 3" in body


def test_list_eyebrow_does_not_read_goal_g(logged_in):
    """The wart: an eyebrow that says "Goal" then "G1" reads as a typo."""
    body = logged_in("Bill Gaudelli").get("/goals/1").text
    assert "Goal G1" not in body, "the eyebrow still glues the word to the abbreviation"


def test_mi_table_keeps_the_short_chip(logged_in):
    """Where five goals share a cell, the short "G1" is right."""
    body = logged_in("Bill Gaudelli").get("/team-initiatives").text
    assert "chip-goal" in body
