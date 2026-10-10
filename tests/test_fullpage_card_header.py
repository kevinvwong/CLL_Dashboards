"""The full-page card renders its header once (change `fix-fullpage-card-duplication`).

The full page used to render the shared card fragment and THEN a second copy of
its header ~950px below, so the code, the level, the name, the description and
the "Contributes to" list each appeared twice, and the page's only `h1` was
rendered after every `h2` it should have introduced.

The two assertions in `test_cards.py` that touch this surface check PRESENCE
(`assert "card-title" in response.text`, `assert "Contributes to" in html`) -
which is exactly what let the duplication ship. These assert COUNT and ORDER,
the properties that would have failed.

The duplicate measurements were taken against the live page for MI-001 before the
fix; the expectations below are the shape the page must hold afterwards.
"""
MARIO = "MI-002"


def _full_page_html(logged_in, code=MARIO):
    return logged_in("Bill Gaudelli").get(f"/team-initiatives/{code}").text


def test_the_full_page_renders_its_header_once(logged_in):
    """Code, level, name and description appear once each - not twice."""
    html = _full_page_html(logged_in)

    # The name once: the page's h1, and not the fragment's card-title.
    assert html.count("<h1") == 1
    assert 'class="card-title"' not in html

    # The code once: the section-heading eyebrow, not the fragment's card-code.
    assert 'class="card-code"' not in html
    assert html.count("· Team Initiative") == 1

    # The description once: rendered by the fragment, not again as mi-description.
    assert 'class="mi-description"' not in html
    assert html.count("class=\"card-description\"") == 1


def test_the_contributes_to_list_appears_once(logged_in):
    """The Dean initiatives are listed once, and it is the copy that carries codes."""
    html = _full_page_html(logged_in)
    assert html.count("Contributes to") == 1
    # The fragment's copy is the one kept: it carries the D27-n code and a link.
    assert 'class="connections"' in html
    assert "/team-initiatives/D27-" in html
    # The removed copy was keyed by its own aria-labelledby id, which no longer
    # exists. (Not `mi-chip-list`: the goals and priorities sections use that
    # class too, so it is not a marker of the removed block.)
    assert "mi-dean-heading" not in html
    # Each Dean is linked once, by its D27-n code, which only the fragment's copy
    # carries. Scoped to the `href` attribute: the same anchor also carries the
    # path in `hx-get`, so a bare path count is two per link, not two per list.
    # (Not the Dean NAME: the source register's free-text `Initiatives` field
    # legitimately contains it too, so a name count is not a duplication signal.)
    for code in ("D27-3", "D27-6"):
        assert html.count(f'href="/team-initiatives/{code}"') == 1, code


def test_the_h1_leads_the_content_it_titles(logged_in):
    """The h1 renders BEFORE the card body - the outline was inverted."""
    html = _full_page_html(logged_in)
    h1 = html.index("<h1")
    body = html.index('class="card-body')
    assert h1 < body, (
        "the page heading must precede the content it titles; "
        f"h1 at {h1}, card-body at {body}"
    )


def test_the_drawer_fragment_keeps_its_own_header(logged_in):
    """The HTMX path still gets code, title and close control - it has no page
    heading to inherit. This is the counterpart to the three tests above."""
    html = logged_in("Bill Gaudelli").get(
        f"/team-initiatives/{MARIO}", headers={"HX-Request": "true"}).text
    assert "<html" not in html
    assert 'class="card-code"' in html
    assert 'class="card-title"' in html
    assert 'class="card-close"' in html
