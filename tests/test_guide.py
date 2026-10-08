"""The in-app guide: single-sourced markdown, curated, and access-controlled.

The guide renders the repository's own docs/*.md (so it cannot drift from the
docs a developer reads), through a manifest that chooses order/group/audience.
User chapters are open to any signed-in person; technical chapters are admin-only
(ADR-0005), enforced by the reader as well as hidden from the index.
"""
import os

import pytest

from app import docs

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_manifest_loads_and_resolves_paths(fresh_db, monkeypatch):
    monkeypatch.setenv("DOCS_PATH", os.path.join(APP, "docs"))
    entries = docs.load_manifest()
    assert entries, "the guide manifest is empty"
    slugs = [e["slug"] for e in entries]
    assert "what-this-is" in slugs and "glossary" in slugs
    # Every user chapter ships; a resolvable path is within the docs root.
    user = [e for e in entries if e["audience"] == "user"]
    assert all(e["exists"] for e in user), [e["slug"] for e in user if not e["exists"]]


def test_a_path_that_escapes_the_docs_root_is_refused(fresh_db, monkeypatch, tmp_path):
    monkeypatch.setenv("DOCS_PATH", os.path.join(APP, "docs"))
    root = docs._docs_root()
    assert docs._safe_join(root, "../secret.md") is None
    assert docs._safe_join(root, "guide/01-what-this-is.md") is not None


def test_markdown_renders_as_html_not_escaped_text(fresh_db, monkeypatch):
    monkeypatch.setenv("DOCS_PATH", os.path.join(APP, "docs"))
    chapter = docs.chapter("what-this-is")
    assert chapter is not None
    html = str(chapter["html"])
    assert "<h1>" in html, "the markdown did not render to HTML"
    assert "&lt;h1" not in html, "the HTML was escaped"


def test_the_guide_index_is_gated(anon):
    r = anon.get("/guide", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_a_user_sees_user_chapters_but_not_technical(logged_in):
    body = logged_in("Bill Gaudelli").get("/guide").text
    assert "/guide/glossary" in body
    assert "/guide/deploying" not in body, "a technical chapter leaked to a non-admin"


def test_a_technical_chapter_is_403_for_a_non_admin(logged_in):
    r = logged_in("Bill Gaudelli").get("/guide/deploying", follow_redirects=False)
    assert r.status_code == 403


def test_an_admin_sees_and_can_open_a_technical_chapter(logged_in):
    body = logged_in("Kevin").get("/guide").text
    assert "/guide/deploying" in body
    r = logged_in("Kevin").get("/guide/deploying")
    assert r.status_code == 200


def test_a_missing_chapter_is_404(logged_in):
    assert logged_in("Kevin").get("/guide/no-such-chapter").status_code == 404


def test_the_nav_offers_the_guide(logged_in):
    body = logged_in("Bill Gaudelli").get("/").text
    assert 'href="/guide"' in body
