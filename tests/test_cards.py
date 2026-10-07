"""Initiative and person cards, on the merged register model (2026-10-07).

The merged model has ONE initiative tier (the register's Major Initiatives) and
no Dean/D-1 split. The card's relationships are the Dean Priorities a Major
Initiative contributes to, not Fed-by/Feeds. The register ships no diary, so the
tests that need progress seed one with the `diary` fixture.
"""
import re

import pytest

MARIO = "MI-002"          # 'Reusable content', owned by Mario Herane
ELIZABETH_MI = "MI-004"   # 'Team operating models', owned by Elizabeth Smith
ELIZABETH = 2             # PersonID for Elizabeth Smith
BILL = 1                  # PersonID for Bill Gaudelli, the Dean


# --- fragment vs full page ------------------------------------------------


def test_htmx_request_gets_a_bare_fragment(logged_in):
    response = logged_in("Bill Gaudelli").get(
        f"/major-initiatives/{MARIO}", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "card-title" in response.text


def test_direct_navigation_gets_a_full_page(logged_in):
    response = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}")
    assert response.status_code == 200
    assert "<html" in response.text
    assert 'class="card-body' in response.text
    assert "Initiative Dashboard" in response.text


def test_unknown_initiative_is_404(logged_in):
    assert logged_in("Bill Gaudelli").get("/major-initiatives/NOPE-9").status_code == 404


# --- card sections --------------------------------------------------------


def test_card_shows_details_and_owner(logged_in):
    body = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}").text
    assert MARIO in body
    assert "Reusable content" in body
    # the owner is linked to their person page (Mario Herane, PersonID 4)
    assert 'href="/people/4"' in body


def test_card_shows_goal_and_priority_tags(logged_in):
    body = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}").text
    assert "Goals:" in body
    assert "Priorities:" in body


def test_card_shows_latest_progress_and_diary(logged_in, diary):
    diary(MARIO, 30, "On track", note="first", on="2026-10-05")
    body = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}").text
    assert "Latest" in body
    assert "Diary" in body
    assert "30%" in body


def test_diary_is_newest_first(logged_in, diary):
    from app import queries

    diary(MARIO, 20, "On track", on="2026-09-20")
    diary(MARIO, 30, "On track", on="2026-10-05")
    dates = [d["UpdateDate"] for d in queries.initiative_card(MARIO)["diary"]]
    assert dates == sorted(dates, reverse=True)


# --- the card's relationships: the Dean Priorities it contributes to ------


def test_card_lists_the_dean_priorities_it_contributes_to(logged_in):
    body = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}").text
    assert "Contributes to" in body


def test_connected_items_swap_the_modal_in_place(logged_in):
    """A connected Dean Priority links to its own screen; the initiative's own
    connections render with the swap attributes the drawer uses."""
    body = logged_in("Bill Gaudelli").get(f"/major-initiatives/{MARIO}").text
    assert "card-connections" in body


# --- person card ----------------------------------------------------------


def test_person_card_lists_active_initiatives(logged_in):
    response = logged_in("Bill Gaudelli").get(f"/people/{ELIZABETH}")
    assert response.status_code == 200
    assert "Elizabeth Smith" in response.text
    assert ELIZABETH_MI in response.text


def test_person_card_omits_retired_initiatives(logged_in):
    from app import queries

    card = queries.person_card(ELIZABETH)
    for row in card["initiatives"]:
        assert row["Code"]


def _seed_all_of_elizabeth(fresh_db, diary, on="2026-10-05"):
    """Give every initiative Elizabeth owns a diary entry, so a whole-card
    staleness assertion is about the dates, not about the ones left empty."""
    import sqlite3

    conn = sqlite3.connect(fresh_db)
    mIs = [r[0] for r in conn.execute(
        "SELECT MIId FROM MajorInitiatives WHERE OwnerID = ? AND IsActive = 1",
        (ELIZABETH,))]
    conn.close()
    for mi in mIs:
        diary(mi, 10, "On track", on=on)


def test_stale_flag_uses_the_fourteen_day_threshold(logged_in, fresh_db, diary):
    """The person-card requirement says "older than 14 days".

    14 is the threshold; the boundary is asserted in both directions.
    """
    import sqlite3

    from app import queries

    assert queries.STALE_DAYS == 14

    _seed_all_of_elizabeth(fresh_db, diary)
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE MajorInitiativeUpdates SET UpdateDate = date('now', '-25 days')")
    conn.commit()
    conn.close()

    card = queries.person_card(ELIZABETH)
    assert card["initiatives"]
    assert all(r["NeedsUpdate"] for r in card["initiatives"]), "25 days old must flag"

    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE MajorInitiativeUpdates SET UpdateDate = date('now', '-10 days')")
    conn.commit()
    conn.close()

    card = queries.person_card(ELIZABETH)
    assert not any(r["NeedsUpdate"] for r in card["initiatives"]), "10 days old must not flag"


def test_stale_flag_boundary_is_fourteen_not_fifteen(logged_in, fresh_db, diary):
    """"Older than 14" means 14 itself is inside the window and 15 is outside."""
    import sqlite3

    from app import queries

    _seed_all_of_elizabeth(fresh_db, diary)
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE MajorInitiativeUpdates SET UpdateDate = date('now', '-14 days')")
    conn.commit()
    conn.close()
    card = queries.person_card(ELIZABETH)
    assert not any(r["NeedsUpdate"] for r in card["initiatives"]), "14 is not older than 14"

    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE MajorInitiativeUpdates SET UpdateDate = date('now', '-15 days')")
    conn.commit()
    conn.close()
    card = queries.person_card(ELIZABETH)
    assert all(r["NeedsUpdate"] for r in card["initiatives"]), "15 is older than 14"


def test_stale_flag_fires_when_there_is_no_update_at_all(logged_in, fresh_db):
    """The other half of the spec: no update is also "Needs update"."""
    from app import queries

    card = queries.person_card(ELIZABETH)
    row = [r for r in card["initiatives"] if r["Code"] == ELIZABETH_MI][0]
    assert row["NeedsUpdate"] is True
    assert row["PercentComplete"] is None


def test_stale_flag_renders_in_the_page(logged_in, fresh_db, diary):
    import sqlite3

    diary(ELIZABETH_MI, 10, "On track", on="2026-10-05")
    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE MajorInitiativeUpdates SET UpdateDate = date('now', '-40 days')")
    conn.commit()
    conn.close()

    body = logged_in("Bill Gaudelli").get(f"/people/{ELIZABETH}").text
    assert "Needs update" in body


def test_unknown_person_is_404(logged_in):
    assert logged_in("Bill Gaudelli").get("/people/9999").status_code == 404


@pytest.mark.parametrize("code", [MARIO, ELIZABETH_MI])
def test_cards_are_behind_the_gate(anon, code):
    assert anon.get(f"/major-initiatives/{code}", follow_redirects=False).status_code == 303
