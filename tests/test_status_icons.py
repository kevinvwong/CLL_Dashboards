"""Status is carried by a shape as well as a colour (WCAG 1.4.1).

A colourblind, greyscale-print, or forced-colours reader cannot tell an "On
track" badge from an "At risk" one by hue alone. Each status now renders a
glyph beside the word; the glyph is decorative (aria-hidden) and the word is
always present, so a screen reader still hears the status.
"""
from app import status


def test_every_status_has_a_glyph():
    for value in status.vocabulary():
        assert status.status_icon(value), "no glyph for %r" % value


def test_unknown_status_has_no_glyph():
    assert status.status_icon("") == ""
    assert status.status_icon("nonsense") == ""


def test_glyphs_are_distinct():
    glyphs = [status.status_icon(v) for v in status.vocabulary()]
    assert len(set(glyphs)) == len(glyphs), "two statuses share a glyph: %s" % glyphs


def test_the_badge_renders_the_glyph_and_the_word(logged_in, diary):
    diary("MI-002", 30, "At risk", on="2026-10-05")
    body = logged_in("Bill Gaudelli").get("/major-initiatives/MI-002").text
    glyph = status.status_icon("At risk")
    assert glyph in body, "the At risk badge did not render its glyph"
    assert "At risk" in body, "the status word must still be present beside the glyph"
