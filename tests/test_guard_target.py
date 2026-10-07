"""Target.card_id: the card's id, with the invariant made explicit.

`Target.card` is `dict | None` because `admin_only` routes carry no card. But
`admin_for` routes ALWAYS resolve one, and they used to reach into
`target.card["InitiativeID"]` directly - three sites a type-checker correctly
flags, because the type says the card might be None. A `card_id` property (the
sibling of `person_id`) states the invariant once, so the routes read cleanly
and a missing card fails loudly rather than raising a bare TypeError.
"""
import pytest

from app.guards import Target


def test_card_id_returns_the_id():
    t = Target(person={"PersonID": 1}, card={"InitiativeID": 42})
    assert t.card_id == 42


def test_card_id_raises_when_there_is_no_card():
    """An admin_only target has no card; asking for its id is a wiring mistake."""
    t = Target(person={"PersonID": 1})
    with pytest.raises(AssertionError):
        _ = t.card_id
