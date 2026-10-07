"""The discreet header stamp: the last push (short commit) and deploy time.

The stamp answers "which version am I looking at?" on the page. It is hidden
when neither is known, which is the committed local-dev state, so a test run
never shows a fake revision. The deploy step sets GIT_COMMIT and DEPLOY_MARKER;
the marker already carries the deploy timestamp, so no second setting is needed.
"""

import pytest

from app import main as mainmod


def test_marker_with_no_timestamp_yields_blank():
    assert mainmod.deploy_time_from_marker("dev") == ""
    assert mainmod.deploy_time_from_marker("") == ""


def test_marker_timestamp_is_read_as_deploy_time():
    assert mainmod.deploy_time_from_marker("plan-20261007T161001Z") == "2026-10-07 16:10 UTC"


def test_label_omits_each_unknown_part():
    assert mainmod.build_stamp_label("", "") == ""
    assert mainmod.build_stamp_label("e1c55d4abcdef", "") == "e1c55d4"
    assert mainmod.build_stamp_label("", "2026-10-07 16:10 UTC") == "deployed 2026-10-07 16:10 UTC"
    assert (
        mainmod.build_stamp_label("e1c55d4abcdef", "2026-10-07 16:10 UTC")
        == "e1c55d4 \u00b7 deployed 2026-10-07 16:10 UTC"
    )


def test_local_dev_hides_the_stamp(logged_in):
    """With neither commit nor deploy time set (the committed state), no stamp."""
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'class="build-stamp"' not in body


def test_deployed_stamp_is_shown(logged_in, monkeypatch):
    """A deployed server renders the commit and deploy time in the header."""
    monkeypatch.setattr(
        mainmod, "BUILD_STAMP_LABEL", "e1c55d4 \u00b7 deployed 2026-10-07 16:10 UTC"
    )
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'class="build-stamp"' in body
    assert "e1c55d4" in body
    assert "deployed 2026-10-07 16:10 UTC" in body


@pytest.mark.parametrize("name", ["Bill Gaudelli", "Kevin"])
def test_stamp_renders_for_any_page_using_the_base(logged_in, monkeypatch, name):
    monkeypatch.setattr(mainmod, "BUILD_STAMP_LABEL", "abc1234 \u00b7 deployed 2026-10-07 16:10 UTC")
    body = logged_in(name).get("/people").text
    assert "abc1234" in body
