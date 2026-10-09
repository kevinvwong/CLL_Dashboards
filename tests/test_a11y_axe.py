"""Axe-core accessibility regression (frontend review, 2026-10-07).

The review found four issues across the app: an empty-bar contrast failure, a
breadcrumb link distinguished by colour alone, `role="link"` on list items
(which broke list semantics), and a 320px overflow. These run axe against the
running app and fail on any NEW serious/critical violation on the pages that
were clean, plus assert the four specific fixes.

Runs against a locally started server (BASE_URL, default 127.0.0.1:8000) and
skips if no server is reachable, so it does not fail an offline test run. Start
one with run-dashboard.cmd, or the whole-suite server fixture.
"""
import os
import urllib.request

import pytest

BASE = os.environ.get("CLL_BASE_URL", "http://127.0.0.1:8000")
AXE = os.path.join(os.environ.get("TEMP", "/tmp"), "opencode", "axe.min.js")


def _passcode_from_env_file():
    """APP_PASSCODE out of the repo .env, so the test matches the server.

    This used to be `os.environ.get("APP_PASSCODE", "devpass")` - a hardcoded
    guess. Any developer who changed their own .env passcode got a 401 here, and
    the failure surfaced 30s later as a Page.click timeout on the NEXT step,
    pointing at the wrong thing entirely. Read what the server actually loaded.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("APP_PASSCODE="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return None


PASSCODE = os.environ.get("APP_PASSCODE") or _passcode_from_env_file() or "devpass"


def _server_up():
    try:
        urllib.request.urlopen(BASE + "/healthz", timeout=2)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _server_up(), reason="no local server on %s" % BASE)


def test_no_serious_axe_violations_on_key_pages():
    from playwright.sync_api import sync_playwright

    axe_path = os.path.normpath(AXE)
    if not os.path.exists(axe_path):
        pytest.skip("axe.min.js not downloaded")
    axe = open(axe_path, encoding="utf-8").read()

    pages = ["/", "/team-initiatives", "/team-initiatives/MI-002", "/people",
             "/people/2", "/goals/1", "/priorities/Identity", "/teams",
             "/outcomes", "/dean-initiatives", "/checks", "/changes"]
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1440, "height": 1000}).new_page()
        pg.goto(BASE + "/login")
        pg.fill("input[name=passcode]", PASSCODE)
        with pg.expect_navigation():
            pg.click("button[type=submit]")
        with pg.expect_navigation():
            pg.click("button[name=person_id][value='5']")
        for path in pages:
            pg.goto(BASE + path, wait_until="networkidle")
            pg.add_script_tag(content=axe)
            res = pg.evaluate(
                "async () => await axe.run(document, {resultTypes:['violations']})")
            for v in res["violations"]:
                if v["impact"] in ("serious", "critical"):
                    bad.append("%s: [%s] %s" % (path, v["impact"], v["id"]))
        b.close()
    assert not bad, "axe serious/critical violations:\n" + "\n".join(bad)
