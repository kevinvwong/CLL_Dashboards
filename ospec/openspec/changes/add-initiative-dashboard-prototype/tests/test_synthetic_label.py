"""Task 8.2 of adopt-rev2-strategy-portfolio-schema: synthetic labelling.

The package ships canonical strategy with zero operational rows
(rev2/inventory-absent.md), so every initiative in this prototype is invented.
These tests assert the label is present wherever an initiative is displayed, in
every environment including live - a reader must not be able to mistake this for
an approved portfolio.
"""


def test_the_banner_shows_in_every_environment(logged_in):
    """Not gated on APP_ENV: the data is invented in production too."""
    body = logged_in("Bill").get("/").text
    assert "synthetic-banner" in body
    assert "invented for this prototype" in body


def test_a_list_row_is_labelled(logged_in):
    body = logged_in("Bill").get("/goals/3").text
    assert "synthetic-label" in body, "every initiative row must carry the label"


def test_the_card_is_labelled(logged_in):
    body = logged_in("Bill").get("/initiatives/ELIZ-1").text
    assert "synthetic-label" in body, "the card must carry the label too"


def test_a_person_page_is_labelled(logged_in):
    body = logged_in("Bill").get("/people/2").text
    assert "synthetic-label" in body


def test_the_meeting_page_is_labelled(logged_in):
    body = logged_in("Bill").get("/meeting").text
    assert "synthetic-label" in body


def test_the_seed_file_says_the_data_is_not_approved():
    """The label has to exist at the point of authorship as well as in the UI,
    or the next person to read the seed will take it for real data."""
    import pathlib
    seed = pathlib.Path(__file__).resolve().parents[4] / "db" / "seed_sample.sql"
    text = seed.read_text(encoding="utf-8")
    assert "NOT GOVERNANCE-APPROVED" in text
    assert "INVENTED" in text