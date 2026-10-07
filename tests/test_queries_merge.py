"""The reads, on the merged register model."""
from app import queries


def test_all_initiatives_reads_the_register(fresh_db):
    rows = queries.all_initiatives()
    assert len(rows) == 29
    assert all(r["Code"].startswith("MI-") for r in rows)


def test_goal_tiles_count_team_initiatives(fresh_db):
    tiles = queries.goal_tiles()
    assert len(tiles) == 5
    assert sum(t["InitiativeCount"] for t in tiles) >= 29


def test_priority_tiles_count_team_initiatives(fresh_db):
    tiles = queries.priority_tiles()
    assert len(tiles) == 6
    assert sum(t["InitiativeCount"] for t in tiles) >= 29


def test_meeting_reads_the_new_diary(fresh_db):
    from app import repo
    repo.add_progress_update("MI-002", 10, "On track", "x", entered_by_id=5)
    groups = queries.meeting_updates(queries.default_since())
    assert groups
    assert any(row["Code"] == "MI-002" for g in groups for row in g["rows"])


def test_initiative_card_resolves_by_mi_id(fresh_db):
    card = queries.initiative_card("MI-002")
    assert card is not None
    assert card["InitiativeName"] == "Reusable content"
    assert card["Code"] == "MI-002"
    assert card["goal_tags"]
    assert card["priority_tags"]


def test_relationships_contribute_to_dean_initiatives(fresh_db):
    rel = queries.relationships_for(["MI-002"])
    assert rel
    for rows in rel.values():
        assert all(r["Direction"] == "Contributes to" for r in rows)
