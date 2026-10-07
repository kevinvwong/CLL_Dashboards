"""Provenance labels after approval (2026-10-07).

The initiatives are now an APPROVED register (approval confirmed 2026-10-07), so
the "invented / not governance-approved" labels that used to follow every
initiative are no longer true and have been removed. This replaces
test_synthetic_label.py, which asserted the opposite while the data was sample.

The OUTCOMES page is a SEPARATE artifact: its six cards' statuses and milestone
counts are hardcoded and are not register data, so its own "Illustrative" marker
STAYS. That distinction is asserted here too, so nobody removes it by mistake.
"""


def test_no_false_invented_label_on_the_home(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert "invented for this prototype" not in body
    assert "not governance-approved" not in body
    assert "sample-banner" not in body, "the sample-data banner should be gone"


def test_no_synthetic_badge_on_a_row_or_card(logged_in):
    for path in ("/goals/3", "/team-initiatives/MI-004", "/people/2"):
        body = logged_in("Bill Gaudelli").get(path).text
        assert "synthetic-label" not in body, path
        assert ">sample<" not in body, path


def test_the_outcomes_marker_stays():
    """The Outcomes page is still illustrative data, not the register."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app import oct16_data as d

    assert d.CONFIRMED is False
    assert "Illustrative" in d.data_status(), d.data_status()


def test_the_approved_initiatives_have_no_sample_text():
    """The 29 rows are register rows; none of their titles says 'sample'."""
    import sqlite3
    from pathlib import Path

    db = Path(__file__).resolve().parents[1] / "cll_initiatives.db"
    con = sqlite3.connect(db)
    n = con.execute(
        "SELECT COUNT(*) FROM TeamInitiatives WHERE LOWER(Title) LIKE '%sample%'").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM TeamInitiatives").fetchone()[0]
    con.close()
    assert total == 29
    assert n == 0, "%d rows still carry 'sample' text" % n
