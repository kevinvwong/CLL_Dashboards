"""Permissions resolve on the register's Team Initiatives."""
from app import auth


def test_the_dean_is_recognised(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Bill Gaudelli")))
    assert auth.is_dean(person) is True


def test_the_admin_is_not_the_dean(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Kevin")))
    assert auth.is_admin(person) is True
    assert auth.is_dean(person) is False


def test_an_owner_may_edit_their_own_team_initiative(fresh_db, request_for, logged_in):
    # Mario Herane (Learning Ecosystems) leads MI-002 'Reusable content'.
    req = request_for(logged_in("Mario Herane"))
    assert auth.can_edit_details(req, "MI-002") is True


def test_a_non_owner_may_not_edit(fresh_db, request_for, logged_in):
    # Tim Jacobbe does not own MI-002.
    req = request_for(logged_in("Tim Jacobbe"))
    assert auth.can_edit_details(req, "MI-002") is False
