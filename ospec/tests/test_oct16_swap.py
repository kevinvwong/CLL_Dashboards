"""The October 16 data swap: dry run, backup, and a layout that does not move.

Covers tasks 4.2-4.3 of launch-initiatives-dashboard-live.

These run the real scripts rather than reimplementing them, because the failure
mode that matters is the script doing something the operator did not see.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(R, "scripts")
swap = os.path.join(SCRIPTS, "swap_oct16_data.py")
MODULE = os.path.join(R, "app", "oct16_data.py")


def _digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _load(path):
    spec = importlib.util.spec_from_file_location("m", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _owners_file(tmp_path, data):
    p = tmp_path / "owners.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _run(args):
    return subprocess.run([sys.executable, swap] + args,
                          capture_output=True, text=True)


@pytest.fixture
def pristine(tmp_path):
    """A copy of the module to compare against.

    The dry-run tests only READ the module, so nothing here swaps the repo. The
    real-swap path is exercised manually per docs/DEPLOY.md, not by the suite: a
    test that writes the committed module would leave the repo swapped if it
    failed halfway.
    """
    work = tmp_path / "oct16_data.py"
    shutil.copy2(MODULE, work)
    return str(work)


# --- the dry run ------------------------------------------------------------


def test_dry_run_reports_the_changes_it_would_make(pristine, tmp_path):
    owners = _owners_file(tmp_path, {"P01": {"owner": "A Person"}})
    p = _run(["--owners", owners, "--dry-run"])
    assert p.returncode == 0, p.stderr
    assert "would make these changes" in p.stdout
    assert "P01 owner" in p.stdout
    assert "A Person" in p.stdout


def test_dry_run_writes_nothing(pristine, tmp_path):
    """The committed module must be byte-identical after a dry run.

    Checks the REAL module, not a copy: the question is whether the dry run
    touches the file the app serves.
    """
    before = _digest(MODULE)
    owners = _owners_file(tmp_path, {"P01": {"owner": "A Person"}})

    p = _run(["--owners", owners, "--dry-run"])
    assert p.returncode == 0, p.stderr
    assert _digest(MODULE) == before, "the dry run modified the committed module"
    assert "DRY RUN" in p.stdout


def test_dry_run_reports_a_no_op_as_a_no_op(pristine, tmp_path):
    """Swapping to the same state must say there is nothing to do."""
    current = _load(pristine)
    owners = _owners_file(tmp_path, {
        o["id"]: {"owner": o["owner"]} for o in current.OUTCOMES
    })
    p = _run(["--owners", owners, "--dry-run"])
    assert p.returncode == 0, p.stderr
    assert "No differences" in p.stdout or "would make these changes" not in p.stdout


def test_an_empty_owners_file_is_refused(pristine, tmp_path):
    """An empty file would silently un-confirm everything."""
    owners = tmp_path / "empty.json"
    owners.write_text("{}", encoding="utf-8")
    p = _run(["--owners", str(owners), "--dry-run"])
    assert p.returncode != 0
    assert "empty" in (p.stdout + p.stderr).lower()


def test_an_unknown_outcome_is_refused(pristine, tmp_path):
    owners = _owners_file(tmp_path, {"NOT-A-REAL-ID": {"owner": "Someone"}})
    p = _run(["--owners", owners, "--dry-run"])
    assert p.returncode != 0, "an unknown outcome id should be refused"


# --- layout does not move ---------------------------------------------------


def test_the_swap_does_not_change_layout(pristine, tmp_path):
    """Same six cards, same section headings, same table size - only values change.

    Task 4.3: a reader must not have to re-learn the page because the data changed.
    """
    before = _load(pristine)
    owners = _owners_file(tmp_path, {"P01": {"owner": "A Person"},
                                     "P02": {"owner": "Another"}})

    staged = os.path.join(tempfile.mkdtemp(), "staged.py")
    generator = os.path.join(SCRIPTS, "build_oct16_data.py")
    p = subprocess.run([sys.executable, generator, "--owners", owners, "--out", staged],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    after = _load(staged)

    assert [o["id"] for o in before.OUTCOMES] == [o["id"] for o in after.OUTCOMES]
    assert [o["name"] for o in before.OUTCOMES] == [o["name"] for o in after.OUTCOMES]
    assert len(before.DATA_REQUIREMENTS) == len(after.DATA_REQUIREMENTS)
    assert [s[0] for s in before.SCOPE] == [s[0] for s in after.SCOPE]
    assert before.TITLE == after.TITLE
    assert before.EYEBROW == after.EYEBROW
    assert before.EXPLAINER == after.EXPLAINER
    assert len(before.TRADE_OFFS) == len(after.TRADE_OFFS)
    # And the milestone NAMES are unchanged: only statuses may move.
    for a, b in zip(before.OUTCOMES, after.OUTCOMES):
        assert [m[0] for m in a["milestones"]] == [m[0] for m in b["milestones"]], (
            "milestone names moved for %s - the swap changed the layout" % a["id"]
        )


def test_a_swap_keeps_the_page_renderable(pristine, tmp_path, logged_in, monkeypatch):
    """The generated module must render, not merely import."""
    import html as _html

    owners = _owners_file(tmp_path, {"P01": {"owner": "A Person"}})
    staged = os.path.join(tempfile.mkdtemp(), "staged.py")
    generator = os.path.join(SCRIPTS, "build_oct16_data.py")
    subprocess.run([sys.executable, generator, "--owners", owners, "--out", staged],
                   capture_output=True, text=True)

    from app import oct16_data as live
    mod = _load(staged)
    monkeypatch.setattr(live, "OUTCOMES", mod.OUTCOMES, raising=True)
    monkeypatch.setattr(live, "CONFIRMED", mod.CONFIRMED, raising=True)

    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "A Person" in body
    assert len(body) > 5000, "the page rendered but looks empty"
