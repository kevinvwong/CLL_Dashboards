"""Status presentation: one vocabulary, one slug, one colour.

Covers the `status-presentation` spec of deepen-dashboard-modules.

Two of these are the checks that would have caught the defects this change
fixes: the milestone classes were emitted with no CSS rule, and a status badge
outside a bar had no colour.
"""
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, "app")
TEMPLATES = os.path.join(SRC, "templates")
CSS = os.path.join(SRC, "static", "style.css")
# APP is the repo root; the schema lives at db/schema.sql.
SCHEMA = os.path.join(APP, "db", "schema.sql")


# --- one vocabulary ---------------------------------------------------------


def test_the_vocabulary_equals_the_schemas_check():
    """The module reads the schema, so a schema change fails this test.

    The schema is the source of truth for the status vocabulary; a second,
    hardcoded list would drift from it.
    """
    from app import repo, status

    schema_text = open(SCHEMA, encoding="utf-8").read()
    m = re.search(r"CHECK\s*\(\s*Status\s+IN\s*\(([^)]*)\)", schema_text)
    assert m, "could not find the Status CHECK in the schema"
    from_schema = [v.strip().strip("'") for v in m.group(1).split(",") if v.strip()]

    assert list(status.vocabulary()) == from_schema
    assert list(status.vocabulary()) == list(repo.STATUSES)


# --- one slug ---------------------------------------------------------------


def test_the_slug_is_stable_for_a_value_with_a_space():
    from app import status

    assert status.slug("At risk") == "at-risk"
    assert status.slug("Not started") == "not-started"
    assert status.status_class("On track") == "status-on-track"
    assert status.milestone_class("In progress") == "m-in-progress"


def test_no_template_reimplements_the_slug():
    """The transform lives in the module, not in six templates."""
    offenders = []
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".html"):
            continue
        text = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        for i, line in enumerate(text.splitlines(), 1):
            if "| lower | replace(' ', '-')" in line or '| lower | replace(" ", "-")' in line:
                offenders.append("%s:%d" % (name, i))
    assert not offenders, (
        "a template still re-implements the status slug:\n" + "\n".join(offenders)
    )


# --- every emitted class has an appearance ---------------------------------


def test_every_milestone_class_has_a_css_rule():
    """The classes oct16.html emits must have rules.

    The milestone status values are DERIVED from the committed data, not typed
    into this test, so a new milestone status cannot be emitted unstyled. This is
    the check that would have caught `m-met` / `m-in-progress` being emitted with
    no rule at all.
    """
    from app import oct16_data, status

    css = open(CSS, encoding="utf-8").read()
    values = {s for o in oct16_data.OUTCOMES for _, s in o["milestones"]}
    assert values, "no milestone statuses found in the data"
    for value in sorted(values):
        cls = status.milestone_class(value)
        assert "." + cls in css, (
            "milestone class %r is emitted by the page but has no CSS rule" % cls
        )


def test_every_availability_class_has_a_css_rule():
    """The availability values are likewise derived from the data.

    Three values (Build, Derived, Have it) were emitted with no rule, the same
    defect as the milestone classes - found while checking this test rather than
    assumed.
    """
    from app import oct16_data, status

    css = open(CSS, encoding="utf-8").read()
    values = {r["available"] for r in oct16_data.DATA_REQUIREMENTS if r["available"]}
    assert values, "no availability values found in the data"
    for value in sorted(values):
        cls = status.availability_class(value)
        assert "." + cls in css, (
            "availability class %r is emitted by the page but has no CSS rule" % cls
        )


def test_a_status_badge_has_a_colour_rule():
    """A status shown as a badge must be coloured, not only a bar fill.

    The spec requires the status to carry its meaning wherever it appears. The
    old CSS scoped every status colour to `.bar-fill.status-*`, so the badge on
    the October 16 cards rendered uncoloured.
    """
    from app import status

    css = open(CSS, encoding="utf-8").read()
    for value in ("On track", "At risk", "Off track", "Not started", "Paused", "Complete"):
        cls = status.status_class(value)
        assert (".badge." + cls) in css, (
            "status badge class %r has no colour rule" % cls
        )


def test_status_classes_are_emitted_by_the_filters():
    """The templates use the filters, so the module is on the render path."""
    page = open(os.path.join(TEMPLATES, "oct16.html"), encoding="utf-8").read()
    assert "| status_class" in page
    assert "| milestone_class" in page
    assert "| availability_class" in page

    row = open(os.path.join(TEMPLATES, "_row.html"), encoding="utf-8").read()
    assert "| status_class" in row


# --- the same status renders the same everywhere ---------------------------


def test_the_same_status_uses_one_class_on_every_screen(logged_in):
    """One status, one class string, on every screen that shows it.

    Renders a page that shows statuses and asserts the class the module produces
    appears - the same string a bar fill and a badge both use, because both call
    the one filter.
    """
    from app import status

    # D-A is On track in the sample data; its bar uses the module's class.
    listing = logged_in("Bill Gaudelli").get("/goals/1").text
    assert status.status_class("On track") in listing, (
        "the list screen did not render the module's status class"
    )

    # The October 16 badge uses the same transform for the same value.
    page = logged_in("Bill Gaudelli").get("/oct16").text
    assert status.status_class("On track") in page, (
        "the October 16 badge did not use the same status class"
    )

