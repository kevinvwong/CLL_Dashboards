"""The overview reads clearly (review round, 2026-10-07).

The merge collapsed two initiative layers into one, so the overview kept
counting both: the stat band showed 29 twice, and every goal tile read
"18 initiatives . 18 Team Initiatives". Those are now one number each. And the
health line distinguished "no progress reported yet" from a genuine all-not-started
scorecard, because the register ships an empty diary.
"""


def test_home_does_not_count_team_initiatives_twice(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    # the stat band must not carry both an "Initiatives" and a "Team Initiatives"
    # tile at 29
    assert body.count('class="stat-value">29<') == 1, "29 is still printed twice"


def test_goal_tile_prints_one_count(logged_in):
    """The wart: "18 initiatives . 18 Team Initiatives" - the same set, twice."""
    import re

    body = logged_in("Bill Gaudelli").get("/").text
    dupes = re.findall(r"(\d+) initiatives? \u00b7 \1 Team Initiatives?", body)
    assert not dupes, "a goal tile prints the same count twice: %s" % dupes


def test_health_line_says_no_progress_reported_when_diary_is_empty(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert "no progress reported yet" in body.lower()


def test_health_line_shows_the_breakdown_once_there_is_progress(logged_in, diary):
    diary("MI-002", 30, "On track", on="2026-10-05")
    body = logged_in("Bill Gaudelli").get("/").text
    assert "no progress reported yet" not in body.lower()
    assert "1 on track" in body
