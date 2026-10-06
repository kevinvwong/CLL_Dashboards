"""Task 3.4 check: the home screen.

The strategy-navigation spec requires 5 goal tiles and 6 priority tiles, each
carrying an initiative count. Counts are asserted against the sample data so
a broken join cannot pass as "some number appeared".
"""

EXPECTED_GOALS = {
    1: ("Academic", 10),
    2: ("Extension", 3),
    3: ("Research", 5),
    4: ("Learner impact", 3),
    5: ("Operational", 8),
}

EXPECTED_PRIORITIES = {
    "Culture": 2,
    "Data": 4,
    "Identity": 3,
    "Innovation": 6,
    "Pathways": 5,
    "Scale": 5,
}


def test_home_shows_five_goal_and_six_priority_tiles(logged_in):
    from app import queries

    response = logged_in("Bill").get("/")
    assert response.status_code == 200

    goals = queries.goal_tiles()
    priorities = queries.priority_tiles()
    assert len(goals) == 5
    assert len(priorities) == 6

    # One anchor per tile, so the counts are tile counts and not stray numbers.
    body = response.text
    for goal in goals:
        assert f"/goals/{goal['GoalNumber']}" in body
    for priority in priorities:
        assert f"/priorities/{priority['PriorityName']}" in body


def test_goal_tile_fields(logged_in):
    from app import queries

    got = {g["GoalNumber"]: (g["ShortName"], g["InitiativeCount"]) for g in queries.goal_tiles()}
    assert got == EXPECTED_GOALS


def test_priority_tile_fields(logged_in):
    from app import queries

    got = {p["PriorityName"]: p["InitiativeCount"] for p in queries.priority_tiles()}
    assert got == EXPECTED_PRIORITIES


def test_tile_counts_appear_in_the_rendered_page(logged_in):
    body = logged_in("Bill").get("/").text
    # "Research 5" and "Innovation 6" as label+count pairs in the markup.
    assert "Research" in body
    assert ">5<" in body
    assert "Innovation" in body
    assert ">6<" in body


def test_home_requires_a_signed_in_person(anon):
    """The gate still applies to the home screen."""
    response = anon.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_nav_and_print_assets_are_present(logged_in):
    body = logged_in("Bill").get("/").text
    assert 'href="/meeting"' in body
    assert 'href="/checks"' in body
    assert 'media="print"' in body
    assert "<dialog" in body