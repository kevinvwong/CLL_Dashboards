"""Goal data correctness: the goals match canonical Strategy 2035.

Covers `goal-data-correctness` from launch-initiatives-dashboard-live. This is the
test that would have caught the transposition: it reads the expected wording from
the canonical source file rather than duplicating it, so editing the source and the
data apart from each other fails here.
"""
import pytest

from app import queries

# Read from the generated source, not retyped. If the deck changes and the source
# is regenerated, these expectations move with it.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
from canonical_goals import GOALS, SOURCE  # noqa: E402

CANONICAL = {n: (short, title) for n, short, title in GOALS}


def _stored():
    """The goals as the running service sees them."""
    return {g["GoalNumber"]: g for g in queries.goal_tiles()}


def test_there_are_exactly_five_goals_numbered_one_to_five(logged_in):
    stored = _stored()
    assert sorted(stored) == [1, 2, 3, 4, 5], "goals must be numbered 1..5"


def test_every_goal_carries_the_canonical_wording(logged_in):
    """Number and wording agree with the source, for all five.

    Fails if a goal's number is changed: the number would then carry a different
    goal's wording. Proven by changing one number and watching this go red.
    """
    stored = _stored()
    for number, (short, title) in CANONICAL.items():
        row = stored[number]
        assert row["ShortName"] == short, (
            "goal %d is %r but the canonical source has %r at that number"
            % (number, row["ShortName"], short)
        )
        assert row["FullName"] == title, (
            "goal %d wording differs from %s" % (number, SOURCE)
        )


def test_no_two_goals_are_transposed(logged_in):
    """Each number carries the goal the source assigns it.

    This is the regression test for the transposition: the seed had the Research
    and Learner goals at 3 and 4, opposite to the deck. It is asserted per number
    rather than by comparing sets, because two transposed goals are still a valid
    set - only their positions are wrong.
    """
    stored = _stored()
    for number, (short, _) in CANONICAL.items():
        assert stored[number]["ShortName"] == short, (
            "the goal at number %d is transposed: found %r, expected %r"
            % (number, stored[number]["ShortName"], short)
        )
    # And the two that were swapped specifically, named so a failure is legible.
    assert stored[3]["ShortName"] == "Learner", "goal 3 must be Learner"
    assert stored[4]["ShortName"] == "Research", "goal 4 must be Research"


def test_no_goal_wording_is_blank(logged_in):
    """Goals 2-5 had no title at all before the correction."""
    stored = _stored()
    for number, row in stored.items():
        assert (row["FullName"] or "").strip(), "goal %d has no canonical title" % number


def test_no_goal_wording_is_a_truncated_paraphrase(logged_in):
    """Goal 1 was truncated to "...and build a home for..." before the correction.

    Asserted by checking the canonical text is present in full, so a shortened
    version cannot satisfy it.
    """
    stored = _stored()
    for number, (_, title) in CANONICAL.items():
        assert title in stored[number]["FullName"], (
            "goal %d does not contain its canonical wording in full" % number
        )


def test_canonical_wording_survives_the_round_trip(logged_in):
    """Non-ASCII must be intact: goal 1 carries a curly apostrophe, goal 3 an en dash."""
    stored = _stored()
    joined = "".join(row["FullName"] for row in stored.values())
    assert "\u2019" in joined, "the curly apostrophe was lost"
    assert "\u2013" in joined, "the en dash was lost"


def test_a_goal_scoped_url_opens_the_goal_that_number_names(logged_in):
    """The canonical source assigns each number a goal; the URL must agree."""
    stored = _stored()
    for number, (short, _) in CANONICAL.items():
        body = logged_in("Bill Gaudelli").get("/goals/%d" % number).text
        assert short in body, (
            "/goals/%d serves the wrong goal: %r not found" % (number, short)
        )


def test_goals_are_not_conflated_with_the_objectives_beneath_them(logged_in):
    """The service presents five goals, not the 25 objectives beneath them.

    The objectives are a separate tier and are not stored here; this asserts the
    goal count is not inflated by them.
    """
    assert len(_stored()) == 5, "the goal count must count goals, not objectives"
