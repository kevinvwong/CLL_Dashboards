"""Group 5 of blueprint-redesign: navigation, coverage, meeting, outcomes.

Covers the hybrid nav and its active state, the stable outcomes route, the user
menu, breadcrumbs, the merged coverage/checks page, and that the meeting and
outcomes pages still render.
"""
import html as _html
import os

import pytest

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 5.1 the hybrid nav ------------------------------------------------------


def test_the_primary_nav_has_the_five_destinations(logged_in):
    """The nav's live destinations. Meeting is ICED (2026-10-06), so it is not
    among them while MEETING_ENABLED is unset."""
    body = logged_in("Bill Gaudelli").get("/").text
    for dest in ("/", "/initiatives", "/people", "/outcomes"):
        assert ('href="%s"' % dest) in body, "missing %s" % dest


def test_the_meeting_nav_item_is_hidden_when_iced(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'href="/meeting"' not in body, "the meeting nav item is still shown"


def test_the_active_destination_is_marked(logged_in):
    body = logged_in("Bill Gaudelli").get("/outcomes").text
    assert 'aria-current="page"' in body


def test_the_nav_collapses_at_a_narrow_width():
    from app.main import templates
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    assert ".nav-toggle:checked ~ .site-nav" in css
    assert "@media (max-width: 640px)" in css


# --- 5.2 the stable outcomes route and breadcrumbs --------------------------


def test_oct16_permanently_redirects_to_outcomes(logged_in):
    r = logged_in("Bill Gaudelli").get("/oct16", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"] == "/outcomes"


def test_outcomes_renders(logged_in):
    r = logged_in("Bill Gaudelli").get("/outcomes")
    assert r.status_code == 200
    assert "<html" in r.text.lower()


def test_an_initiative_full_page_shows_breadcrumbs(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/major-initiatives/MI-002").text)
    assert "breadcrumb" in body
    assert "Overview" in body
    assert "Initiatives" in body


def test_the_drawer_fragment_has_no_breadcrumbs(logged_in):
    """Crumbs are the full page's job; the drawer sits over a page with them."""
    body = logged_in("Bill Gaudelli").get("/major-initiatives/MI-002",
                                headers={"HX-Request": "true"}).text
    assert "breadcrumb" not in body


# --- 5.3 the user menu -------------------------------------------------------


def test_the_user_menu_holds_switch_user(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/").text)
    assert "user-menu" in body
    assert "Switch user" in body


def test_switch_user_is_not_in_the_primary_nav(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    nav = body[body.find("<nav"):body.find("</nav>")]
    assert "Switch" not in nav


def test_outcomes_and_checks_are_one_step_from_any_page(logged_in):
    for page in ("/", "/initiatives", "/people"):
        body = logged_in("Bill Gaudelli").get(page).text
        assert 'href="/outcomes"' in body
    # Meeting is iced, so it is not linked from anywhere.
    assert 'href="/meeting"' not in logged_in("Bill Gaudelli").get("/").text


def test_an_admin_sees_the_checks_entry_with_a_count(logged_in):
    body = _html.unescape(logged_in("Kevin").get("/").text)
    assert 'href="/checks"' in body
    assert "nav-admin" in body


def test_a_non_admin_sees_no_checks_entry(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'href="/checks"' not in body


# --- 5.4 coverage merged into the checks page --------------------------------


def test_the_page_has_two_sections(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/checks").text)
    assert "Checks" in body
    assert "Coverage" in body
    # Each section names its own question.
    assert "Data quality" in body or "Data checks" in body
    assert "Design readiness" in body


def test_coverage_is_counts_not_performance(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/checks").text)
    assert "Target completeness, not performance" in body
    assert "coverage-row" in body


def test_coverage_summary_reports_counts():
    from app import queries
    cov = queries.coverage_summary()
    assert cov["total"] == 11  # 5 goals + 6 priorities
    assert 0 <= cov["covered"] <= cov["total"]
    assert "goals" in cov and "priorities" in cov


def test_checks_lists_each_rule_with_its_records(logged_in):
    from app import queries
    checks = queries.data_checks()
    body = _html.unescape(logged_in("Bill Gaudelli").get("/checks").text)
    for c in checks:
        assert c["Code"] in body


# --- 5.5/5.6 meeting (iced) and outcomes restyle ----------------------------


def test_the_meeting_route_is_iced(logged_in):
    """Hidden and disabled (2026-10-06): a bookmarked URL gets a clean 404."""
    assert logged_in("Bill Gaudelli").get("/meeting").status_code == 404


def test_the_outcomes_page_prints_without_chrome():
    css = open(os.path.join(APP, "app", "static", "style.css"), encoding="utf-8").read()
    assert "@media print" in css
    assert ".site-nav, .nav-toggle-label { display: none; }" in css


def test_outcomes_shows_the_six_outcomes(logged_in):
    body = _html.unescape(logged_in("Bill Gaudelli").get("/outcomes").text)
    assert "oct16-grid" in body or "oct16-card" in body
