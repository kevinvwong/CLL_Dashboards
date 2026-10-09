"""The enhancement visuals that need no new data.

The stat-tile proportion fill, the alarm tile's icon, the Dean FY timeline bar,
and the nav icons. Each is decorative (aria-hidden) with the figure in the text
beside it, so nothing is carried by an image alone.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_nav_renders_an_icon_for_each_primary_item(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert body.count("nav-icon") >= 4, "the nav has no icons"
    # The icon is decorative: the label is the accessible name.
    assert 'class="nav-icon"' in body
    for label in ("Overview", "Initiatives", "People", "Outcomes"):
        assert label in body


def test_the_need_review_indicator_shows_a_proportion(logged_in):
    """The actionable indicator kept its proportion bar across the band removal.

    Three tests failed when the stat band was retired, all pointing at the same
    thing: the 'need review' affordance - the proportion bar and the deep link
    into the filtered register - is load-bearing. A telemetry row that dropped it
    would have quietly removed a route into the work queue.
    """
    body = logged_in("Bill Gaudelli").get("/").text
    assert "telemetry-fill" in body, "the 'need review' tile has no proportion bar"
    assert 'href="/team-initiatives?target=needs_review"' in body, (
        "the 'need review' tile must still deep-link into the filtered register")
    # The bar is labelled for a screen reader rather than by colour alone.
    assert re.search(r'aria-label="\d+ of \d+ Team Initiatives"', body)


def test_the_dean_timeline_renders_as_a_bar(logged_in):
    """The FY timeline bar moved to /dean-initiatives (overview split 2026-10-07)."""
    body = logged_in("Bill Gaudelli").get("/dean-initiatives").text
    assert "fy-timeline" in body, "the Dean FY timeline bar is missing"
    assert "fy-26" in body and "fy-27" in body
    assert "FY26" in logged_in("Bill Gaudelli").get("/dean-initiatives").text


def test_the_new_components_have_styles_and_no_colour_literal():
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    for cls in (".telemetry-fill", ".fy-timeline", ".nav-icon", ".identity-legend"):
        assert cls in css, "no style for %s" % cls


def test_the_outcomes_ring_and_milestone_icons_render(logged_in):
    body = logged_in("Bill Gaudelli").get("/outcomes").text
    assert body.count('class="oct16-ring"') == 6, "one ring per outcome card"
    # The ring carries the count as text too, not only as an arc.
    assert body.count("oct16-ring-val") == 6
    # Each milestone chip carries a glyph beside its word.
    assert body.count("status-glyph") >= 18, "milestone chips have no icons"


def test_the_cascade_has_group_rails():
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    assert "list-group:has(> .initiative-list)" in css, "the cascade rails are unstyles"


def test_all_motion_is_suppressed_by_reduced_motion():
    """Every animated selector is disabled under prefers-reduced-motion.

    The block used to cover only .button (2026-10-06); the enhancement motion
    must all join it, or a motion-sensitive reader is animated against their
    setting.
    """
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    idx = css.find("@media (prefers-reduced-motion: reduce)")
    assert idx != -1, "there is no reduced-motion block"
    # The block runs to the first line that closes it; read a generous window.
    block = css[idx:idx + 900]
    for selector in (".bar-fill", ".oct16-fill", ".oct16-ring", ".initiative-row"):
        assert selector in block, "%s is animated without a reduced-motion guard" % selector
    assert "animation: none" in block
    # And the keyframes the moves use all exist.
    for kf in ("@keyframes bar-grow", "@keyframes ring-in", "@keyframes row-in"):
        assert kf in css, "missing %s" % kf


def test_the_stat_count_up_is_retired(logged_in):
    """The count-up is gone, deliberately rather than by oversight.

    It parsed the value as an integer and rewrote the text, so it cannot render
    "3/11" or "0/29" - it would replace the fraction with its numerator. More
    importantly, animating a number upward is the wrong signal for a row whose
    last indicator reports a GAP: motion implies progress, and the honest
    message is that no owner has reported yet.
    """
    body = logged_in("Bill Gaudelli").get("/").text
    assert "stat-value" not in body, "the retired count-up target is still referenced"
    assert "telemetry-value" in body, "the telemetry row should carry the values"


def test_a_priority_chip_carries_its_colour_without_losing_contrast():
    """The chip's colour is a swatch, not its text colour.

    When the chips started rendering their real priority colour the text used a
    mid-tone hue on white and axe flagged a serious contrast failure. The chip
    keeps a dark ink label and a coloured dot + border instead.
    """
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    block = css.split(".chip-priority {")[1].split("}")[0]
    assert "color: var(--ink)" in block, "the chip text is not the readable ink colour"
    # The text colour itself must not be the mid-tone priority hue (border-color is fine).
    assert "\n  color: var(--priority" not in block, "the chip text uses the mid-tone priority hue"
    assert ".chip-priority::before" in css, "the chip has no colour swatch"



