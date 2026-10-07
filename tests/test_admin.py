"""Task 8.9 check: admin editing.

Covers the admin-editing spec - 403 from the server on admin routes, the
"Only one primary goal is allowed" message, and AuditLog rows - plus the
retire and create behaviours from task 8.4.
"""

import sqlite3

import pytest

D1 = "MI-004"
DEAN = "MI-002"
ADMIN = "Kevin"      # the only admin in the sample data
NOT_ADMIN = "Elizabeth Smith"


def _rows(fresh_db, sql, params=()):
    conn = sqlite3.connect(fresh_db)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute(sql, params)]
    conn.close()
    return out


def _initiative_id(fresh_db, code):
    """The MajorInitiativeID for a code, so a screen-read test can call the read.

    The screen-shaped reads (link_edit_options, tag_edit_options) take an
    initiative id; the tests know codes. Rather than re-implementing the read's
    own lookup, this resolves the id from the seeded database.
    """
    return _rows(fresh_db, "SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId = ?",
                 (code,))[0]["MajorInitiativeID"]


ADMIN_ROUTES = [
    ("get", "/major-initiatives/MI-004/edit/tags"),
    ("get", "/major-initiatives/MI-004/edit/links"),
    ("get", "/major-initiatives/new"),
    ("get", "/entries/goal/3/edit"),
    ("get", "/entries/priority/Data/edit"),
]


# --- 8.9: 403 on admin routes ---------------------------------------------


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_non_admin_gets_403_on_admin_routes(logged_in, method, path):
    response = getattr(logged_in(NOT_ADMIN), method)(path)
    assert response.status_code == 403


def test_non_owner_post_gets_403_not_a_silent_success(logged_in, fresh_db):
    """The spec is explicit: the server responds 403 and nothing changes.

    Tim Jacobbe is used rather than NOT_ADMIN because Elizabeth Smith *owns* MI-004 and is
    therefore allowed to edit it - owner-or-admin, per design decision 5.
    """
    before = _rows(fresh_db, "SELECT Title AS InitiativeName FROM MajorInitiatives WHERE MIId = ?", (D1,))
    response = logged_in("Tim Jacobbe").post(
        f"/major-initiatives/{D1}/edit/details", data={"name": "Hijacked"}
    )
    assert response.status_code == 403
    after = _rows(fresh_db, "SELECT Title AS InitiativeName FROM MajorInitiatives WHERE MIId = ?", (D1,))
    assert after == before


def test_admin_is_allowed_on_the_same_routes(logged_in):
    client = logged_in(ADMIN)
    assert client.get(f"/major-initiatives/{D1}/edit/tags").status_code == 200
    assert client.get(f"/major-initiatives/{D1}/edit/links").status_code == 200
    assert client.get("/major-initiatives/new").status_code == 200


def test_owner_may_edit_details_but_not_tags(logged_in):
    assert logged_in("Elizabeth Smith").get(f"/major-initiatives/{D1}/edit/details").status_code == 200
    assert logged_in("Elizabeth Smith").get(f"/major-initiatives/{D1}/edit/tags").status_code == 403


# --- 8.9: primary-tag error message ---------------------------------------


def test_second_primary_priority_is_refused(logged_in, fresh_db):
    """The form's radios can only ever submit one primary, so this scenario is
    reachable only by a hand-crafted POST. The server must refuse it rather than
    quietly keep the first value. Goals carry no primary on the register model;
    priorities do."""
    before = _rows(fresh_db, "SELECT * FROM MajorInitiativePriorities WHERE MajorInitiativeID = "
                             "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId=?)", (D1,))
    response = logged_in(ADMIN).post(
        f"/major-initiatives/{D1}/edit/tags",
        data={"priority": ["1", "2"], "priority_primary": ["1", "2"]},
    )
    assert response.status_code == 422
    assert "Only one primary priority is allowed" in response.text
    after = _rows(fresh_db, "SELECT * FROM MajorInitiativePriorities WHERE MajorInitiativeID = "
                            "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId=?)", (D1,))
    assert after == before, "a refused tag write must change nothing"


def test_one_primary_priority_is_accepted(logged_in, fresh_db):
    response = logged_in(ADMIN).post(
        f"/major-initiatives/{D1}/edit/tags",
        data={"priority": ["1", "2"], "priority_primary": "1"},
    )
    assert response.status_code == 200
    primaries = _rows(
        fresh_db,
        "SELECT PriorityID FROM MajorInitiativePriorities WHERE IsPrimary = 1 AND MajorInitiativeID = "
        "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId = ?)",
        (D1,),
    )
    assert len(primaries) == 1


def test_tags_are_replaced_not_appended(logged_in, fresh_db):
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/tags", data={"goal": "3"})
    rows = _rows(
        fresh_db,
        "SELECT GoalID FROM MajorInitiativeGoals WHERE MajorInitiativeID = "
        "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId = ?)",
        (D1,),
    )
    assert [r["GoalID"] for r in rows] == [3], "only the submitted tag should remain"


# --- 8.9: audit rows ------------------------------------------------------


def test_edit_details_writes_an_audit_row(logged_in, fresh_db):
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/details",
                          data={"name": "Renamed initiative", "description": "new text"})
    rows = _rows(fresh_db, "SELECT * FROM AuditLog WHERE EntityKey = ? ORDER BY AuditID DESC", (D1,))
    assert rows, "an edit must be audited"
    assert rows[0]["Action"] == "update_initiative"
    assert "Renamed initiative" in rows[0]["Details"]
    assert rows[0]["PersonID"] is not None


def test_audit_row_records_the_person_who_made_the_change(logged_in, fresh_db):
    kevin = _rows(fresh_db, "SELECT PersonID FROM People WHERE Name = 'Kevin'")[0]["PersonID"]
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/details",
                          data={"name": "Renamed again", "description": ""})
    rows = _rows(fresh_db, "SELECT PersonID FROM AuditLog WHERE EntityKey = ?", (D1,))
    assert rows[0]["PersonID"] == kevin


def test_tag_edit_is_audited(logged_in, fresh_db):
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/tags", data={"goal": "1"})
    rows = _rows(fresh_db, "SELECT Action FROM AuditLog WHERE EntityKey = ?", (D1,))
    assert "replace_tags" in [r["Action"] for r in rows]


def test_rename_changes_details_immediately(logged_in):
    body = logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/details",
                                 data={"name": "Brand new name", "description": "d"}).text
    assert "Brand new name" in body


def test_empty_name_is_refused(logged_in, fresh_db):
    before = _rows(fresh_db, "SELECT Title AS InitiativeName FROM MajorInitiatives WHERE MIId = ?", (D1,))
    response = logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/details", data={"name": "   "})
    assert response.status_code == 422
    after = _rows(fresh_db, "SELECT Title AS InitiativeName FROM MajorInitiatives WHERE MIId = ?", (D1,))
    assert after == before


# --- 8.3 links ------------------------------------------------------------


def test_links_only_list_dean_priorities(logged_in, fresh_db):
    from app import queries

    options = queries.link_edit_options(_initiative_id(fresh_db, D1))["deans"]
    assert options
    # The merged model links to Dean Priorities (D27-n), not Dean initiatives.
    assert all(o["Code"].startswith("D") for o in options), [o["Code"] for o in options]


def test_link_edit_saves_the_selection(logged_in, fresh_db):
    from app import queries

    dean_id = queries.link_edit_options(_initiative_id(fresh_db, D1))["deans"][0]["InitiativeID"]
    response = logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/links",
                                     data={"dean_initiative_id": str(dean_id)})
    assert response.status_code == 200
    links = _rows(fresh_db, "SELECT DeanPriorityID FROM MajorInitiativeDeanLinks WHERE MajorInitiativeID = "
                            "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId = ?)", (D1,))
    assert [r["DeanPriorityID"] for r in links] == [dean_id]


def test_linking_to_a_non_dean_priority_is_refused(logged_in, fresh_db):
    """Every target must be a real Dean Priority."""
    response = logged_in(ADMIN).post(f"/major-initiatives/{D1}/edit/links",
                                     data={"dean_initiative_id": "9999"})
    assert response.status_code == 422
    assert "real Dean Priorities" in response.text or "Links must point" in response.text


# --- 8.4 create and retire ------------------------------------------------


def test_create_makes_an_untagged_initiative_that_shows_on_checks(logged_in, fresh_db):
    from app import queries

    owner = _rows(fresh_db, "SELECT PersonID FROM People WHERE Name = 'Elizabeth Smith'")[0]["PersonID"]
    response = logged_in(ADMIN).post("/major-initiatives", data={
        "code": "MI-900", "name": "Brand new", "owner_id": str(owner), "description": "",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/checks"

    issues = {i["Code"] for i in queries.data_checks()}
    assert "MI-900" in issues, "a new initiative has no tags or links yet"


def test_duplicate_code_is_refused_with_a_readable_message(logged_in, fresh_db):
    owner = _rows(fresh_db, "SELECT PersonID FROM People WHERE Name = 'Elizabeth Smith'")[0]["PersonID"]
    existing_code = _rows(fresh_db, "SELECT Code FROM MajorInitiatives WHERE MIId = ?", (D1,))[0]["Code"]
    response = logged_in(ADMIN).post("/major-initiatives", data={
        "code": existing_code, "name": "Clash", "owner_id": str(owner), "description": "",
    })
    assert response.status_code == 422
    assert "already an initiative with the code" in response.text
    assert "sqlite3" not in response.text.lower()


def test_non_admin_cannot_create(logged_in, fresh_db):
    owner = _rows(fresh_db, "SELECT PersonID FROM People WHERE Name = 'Elizabeth Smith'")[0]["PersonID"]
    response = logged_in(NOT_ADMIN).post("/major-initiatives", data={
        "code": "NEW-1", "name": "Nope", "owner_id": str(owner), "description": "",
    })
    assert response.status_code == 403


def test_retire_hides_the_initiative_but_keeps_its_history(logged_in, fresh_db):
    before = _rows(fresh_db, "SELECT COUNT(*) c FROM MajorInitiativeUpdates WHERE MajorInitiativeID = "
                             "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId=?)", (D1,))[0]["c"]
    response = logged_in(ADMIN).post(f"/major-initiatives/{D1}/retire", follow_redirects=False)
    assert response.status_code == 303

    row = _rows(fresh_db, "SELECT IsActive FROM MajorInitiatives WHERE MIId = ?", (D1,))[0]
    assert row["IsActive"] == 0
    after = _rows(fresh_db, "SELECT COUNT(*) c FROM MajorInitiativeUpdates WHERE MajorInitiativeID = "
                            "(SELECT MajorInitiativeID FROM MajorInitiatives WHERE MIId=?)", (D1,))[0]["c"]
    assert after == before, "retire must keep the diary"

    # and it disappears from the list screens
    assert D1 not in logged_in("Bill Gaudelli").get("/goals/1").text


def test_retired_initiative_card_is_404(logged_in):
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/retire", follow_redirects=False)
    assert logged_in("Bill Gaudelli").get(f"/major-initiatives/{D1}").status_code == 404


def test_non_admin_cannot_retire(logged_in, fresh_db):
    response = logged_in(NOT_ADMIN).post(f"/major-initiatives/{D1}/retire", follow_redirects=False)
    assert response.status_code == 403
    assert _rows(fresh_db, "SELECT IsActive FROM MajorInitiatives WHERE MIId = ?", (D1,))[0]["IsActive"] == 1


def test_retiring_twice_is_a_404(logged_in):
    """Once retired the initiative is no longer active, so the route's
    existence check answers 404 rather than reaching the already-retired
    branch in repo. Pinned so the behaviour is deliberate."""
    logged_in(ADMIN).post(f"/major-initiatives/{D1}/retire", follow_redirects=False)
    assert logged_in(ADMIN).post(f"/major-initiatives/{D1}/retire").status_code == 404


# --- 8.4 goal and priority descriptions -----------------------------------


def test_goal_description_edit(logged_in, fresh_db):
    response = logged_in(ADMIN).post("/entries/goal/3/edit",
                                     data={"description": "Catalyse a learning society."},
                                     follow_redirects=False)
    assert response.status_code == 303
    row = _rows(fresh_db, "SELECT Description FROM Goals WHERE GoalNumber = 3")[0]
    assert row["Description"] == "Catalyse a learning society."
    assert "update_goal_description" in [
        r["Action"] for r in _rows(fresh_db, "SELECT Action FROM AuditLog")
    ]


def test_priority_description_edit(logged_in, fresh_db):
    logged_in(ADMIN).post("/entries/priority/Data/edit",
                          data={"description": "One source of truth."},
                          follow_redirects=False)
    row = _rows(fresh_db, "SELECT Description FROM Priorities WHERE PriorityName = 'Data'")[0]
    assert row["Description"] == "One source of truth."


def test_non_admin_cannot_edit_descriptions(logged_in, fresh_db):
    before = _rows(fresh_db, "SELECT Description FROM Goals WHERE GoalNumber = 3")[0]
    assert logged_in(NOT_ADMIN).post("/entries/goal/3/edit",
                                     data={"description": "hijack"}).status_code == 403
    assert _rows(fresh_db, "SELECT Description FROM Goals WHERE GoalNumber = 3")[0] == before


# --- control visibility ---------------------------------------------------


def test_admin_controls_are_hidden_from_a_non_admin(logged_in):
    body = logged_in(NOT_ADMIN).get(f"/major-initiatives/{D1}").text
    assert "Edit tags" not in body
    assert "Retire" not in body


def test_admin_controls_are_shown_to_an_admin(logged_in):
    body = logged_in(ADMIN).get(f"/major-initiatives/{D1}").text
    assert "Edit tags" in body
    assert "Edit links" in body
    assert "Retire" in body