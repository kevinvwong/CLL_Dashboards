"""The progress log must match git history (see scripts/build_progress_log.py).

The log is generated for a non-technical reader and committed. If a commit lands
without regenerating it, the committed page silently describes an older tree, so
this test fails and names the fix. It skips when git history is not available
(a source tarball), so it never fails for the wrong reason.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_progress_log.py"


def _git_available():
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-dir"],
                           capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


pytestmark = pytest.mark.skipif(not _git_available(), reason="no git history here")


def test_progress_log_is_current():
    """`--check` compares the committed log against a fresh build."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr).strip()


def test_progress_log_exists():
    assert (ROOT / "docs" / "ops" / "PROGRESS_LOG.md").exists()
