"""Every template must PARSE.

Added 2026-10-09 after three separate edits to templates left them syntactically
invalid: the test suite caught it, but only incidentally, on whichever screen
happened to render that fragment. Two of them were edits whose oldString ended
mid-line, which silently swallowed the remainder of the line.

This parses all templates directly, so a broken one fails here in milliseconds
instead of surfacing as an unrelated-looking failure somewhere else.

It parses with the APP's own Jinja environment, not a bare one. A bare
Environment has no `priority_label` / `status_class` / `goal_icon` registered,
so it reports "No filter named ..." for perfectly valid templates - which is a
statement about the probe, not about the template, and is exactly the kind of
instrument that cries wolf on correct input.
"""
import pathlib

import pytest

APP = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = APP / "app" / "templates"


def _app_env():
    from app import main
    return main.templates.env


@pytest.mark.parametrize(
    "name", sorted(p.name for p in TEMPLATES.glob("*.html"))
)
def test_the_template_parses(name):
    env = _app_env()
    try:
        env.get_template(name)
    except Exception as exc:  # noqa: BLE001 - the message is the assertion
        pytest.fail("%s does not parse: %s" % (name, exc))


def test_there_are_templates_to_check():
    assert len(list(TEMPLATES.glob("*.html"))) > 10, "template glob found nothing"