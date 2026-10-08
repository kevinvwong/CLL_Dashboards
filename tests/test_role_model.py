"""DR-23: the Executive Sponsor has no routine update authority.

Dean status shall not satisfy `may_update` or any routine data-maintenance
authorization. The Dean authorizes change through an executive action; Strategic
Operations (Operator) or the owner performs it. These tests pin that separation so
re-adding `is_dean` to a general update guard fails loudly.
"""
import sqlite3

from app import auth


def _roles(db, name):
    conn = sqlite3.connect(db)
    try:
        return {r[0] for r in conn.execute(
            "SELECT r.Name FROM PeopleRoles pr JOIN People p ON p.PersonID=pr.PersonID "
            "JOIN Roles r ON r.RoleID=pr.RoleID WHERE p.Name = ?", (name,))}
    finally:
        conn.close()


def test_the_six_canonical_roles_are_seeded(fresh_db):
    conn = sqlite3.connect(fresh_db)
    try:
        names = {r[0] for r in conn.execute("SELECT Name FROM Roles")}
    finally:
        conn.close()
    assert names == {"Administrator", "ExecutiveSponsor", "DataOwner",
                     "Operator", "Contributor", "Viewer"}


def test_the_role_model_is_not_a_hierarchy(fresh_db):
    """The Dean is ExecutiveSponsor, not an elevated Operator (DR-23)."""
    assert "ExecutiveSponsor" in _roles(fresh_db, "Bill Gaudelli")
    assert "Operator" not in _roles(fresh_db, "Bill Gaudelli")


def test_executive_sponsor_holds_executive_not_maintenance_capability(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Bill Gaudelli")))
    assert auth.is_executive_sponsor(person) is True
    assert auth.has_capability(person, "execute_action") is True
    assert auth.has_capability(person, "maintain_data") is False
    assert auth.has_capability(person, "govern_data") is False
    assert auth.has_capability(person, "contribute") is False


def test_operator_holds_maintenance_not_executive_capability(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Kevin")))
    assert auth.has_capability(person, "maintain_data") is True
    assert auth.is_executive_sponsor(person) is False


def test_the_data_owner_is_elizabeth(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Elizabeth Smith")))
    assert auth.has_capability(person, "govern_data") is True


def test_the_dean_cannot_append_an_update_to_any_initiative(fresh_db, request_for, logged_in):
    req = request_for(logged_in("Bill Gaudelli"))
    for mi in ("MI-001", "MI-002", "MI-004"):
        assert auth.can_update(req, mi) is False
