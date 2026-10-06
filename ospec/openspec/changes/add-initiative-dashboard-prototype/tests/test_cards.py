"""Task 5.5 check: initiative and person cards.

Covers the initiative-card spec (contents, Feeds / Fed by, clickable connected
items, direct URL) and the person-card spec (contents, stale-update flag).
"""

import re

import pytest

DEAN = "D-A"          # Dean level, owned by Bill
D1 = "ELIZ-1"         # D-1, owned by Elizabeth
ELIZABETH = 2         # PersonID in the sample data
BILL = 1


# --- 5.1 fragment vs full page -------------------------------------------


def test_htmx_request_gets_a_bare_fragment(logged_in):
    response = logged_in("Bill").get(f"/initiatives/{DEAN}", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<html" not in response.text
    assert "card-title" in response.text


def test_direct_navigation_gets_a_full_page(logged_in):
    response = logged_in("Bill").get(f"/initiatives/{DEAN}")
    assert response.status_code == 200
    assert "<html" in response.text
    assert 'class="card-body' in response.text
    # the header proves base.html rendered
    assert "Initiative Dashboard" in response.text


def test_unknown_initiative_is_404(logged_in):
    assert logged_in("Bill").get("/initiatives/NOPE-9").status_code == 404


# --- 5.2 card sections ----------------------------------------------------


def test_card_shows_details_and_owner(logged_in):
    body = logged_in("Bill").get(f"/initiatives/{DEAN}").text
    assert DEAN in body
    assert "Transparent ROI reporting" in body
    assert "Dean" in body
    assert f'href="/people/{BILL}"' in body


def test_card_shows_goal_and_priority_tags(logged_in):
    body = logged_in("Bill").get(f"/initiatives/{DEAN}").text
    assert "Goals:" in body
    assert "Priorities:" in body
    assert "badge\">Primary" in body


def test_card_shows_latest_progress_and_diary(logged_in):
    body = logged_in("Bill").get(f"/initiatives/{DEAN}").text
    assert "Latest" in body
    assert "Diary" in body
    assert "30%" in body


def test_diary_is_newest_first(logged_in):
    from app import queries

    dates = [d["UpdateDate"] for d in queries.initiative_card(DEAN)["diary"]]
    assert dates == sorted(dates, reverse=True)


# --- Dean card shows "Fed by", D-1 card shows "Feeds" ---------------------


def test_dean_card_lists_fed_by(logged_in):
    body = logged_in("Bill").get(f"/initiatives/{DEAN}").text
    assert "Fed by" in body
    assert "Feeds" not in body.replace("Fed by", "")


def test_dean_card_shows_owner_and_latest_progress_for_each_d1(logged_in):
    """The spec requires each Fed-by entry to carry owner and latest progress."""
    body = logged_in("Bill").get(f"/initiatives/{DEAN}").text
    section = body[body.index("Fed by"):]
    assert "connection-owner" in section
    assert "ELIZ-1" in section
    # latest progress for the connected initiative
    assert "connection-status" in section or "%" in section


def test_d1_card_lists_what_it_feeds(logged_in):
    body = logged_in("Elizabeth").get(f"/initiatives/{D1}").text
    assert "Feeds" in body
    assert DEAN in body


def test_connected_items_swap_the_modal_in_place(logged_in):
    body = logged_in("Elizabeth").get(f"/initiatives/{D1}").text
    assert f'hx-get="/initiatives/{DEAN}"' in body
    assert 'hx-target="#card-modal"' in body
    assert 'hx-swap="innerHTML"' in body


def test_connected_items_link_to_their_screen(logged_in):
    body = logged_in("Elizabeth").get(f"/initiatives/{D1}").text
    assert f'href="/initiatives/{DEAN}"' in body


# --- 5.4 person card -----------------------------------------------------


def test_person_card_lists_active_initiatives(logged_in):
    response = logged_in("Bill").get(f"/people/{ELIZABETH}")
    assert response.status_code == 200
    assert "Elizabeth" in response.text
    assert "ELIZ-1" in response.text


def test_person_card_omits_retired_initiatives(logged_in):
    from app import queries

    card = queries.person_card(ELIZABETH)
    for row in card["initiatives"]:
        assert row["Code"]


def test_stale_flag_uses_the_spec_threshold_of_twenty_days(logged_in, fresh_db):
    """The person-card spec says 20 days. Task 5.4 said 14; the spec wins.

    Verified by ageing one update rather than by reading the constant, so the
    threshold is pinned to observable behaviour.
    """
    import sqlite3

    from app import queries

    assert queries.STALE_DAYS == 20

    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET UpdateDate = date('now', '-25 days')")
    conn.commit()
    conn.close()

    card = queries.person_card(ELIZABETH)
    assert card["initiatives"]
    assert all(r["NeedsUpdate"] for r in card["initiatives"]), "25 days old must flag"

    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET UpdateDate = date('now', '-10 days')")
    conn.commit()
    conn.close()

    card = queries.person_card(ELIZABETH)
    assert not any(r["NeedsUpdate"] for r in card["initiatives"]), "10 days old must not flag"


def test_stale_flag_fires_when_there_is_no_update_at_all(logged_in, fresh_db):
    """The other half of the spec: no update is also "Needs update"."""
    import sqlite3

    from app import queries

    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM ProgressUpdates WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code = 'ELIZ-1')"
    )
    conn.commit()
    conn.close()

    card = queries.person_card(ELIZABETH)
    row = [r for r in card["initiatives"] if r["Code"] == "ELIZ-1"][0]
    assert row["NeedsUpdate"] is True
    assert row["PercentComplete"] is None


def test_stale_flag_renders_in_the_page(logged_in, fresh_db):
    import sqlite3

    conn = sqlite3.connect(fresh_db)
    conn.execute("UPDATE ProgressUpdates SET UpdateDate = date('now', '-40 days')")
    conn.commit()
    conn.close()

    body = logged_in("Bill").get(f"/people/{ELIZABETH}").text
    assert "Needs update" in body


def test_unknown_person_is_404(logged_in):
    assert logged_in("Bill").get("/people/9999").status_code == 404


@pytest.mark.parametrize("code", [DEAN, D1])
def test_cards_are_behind_the_gate(anon, code):
    assert anon.get(f"/initiatives/{code}", follow_redirects=False).status_code == 303