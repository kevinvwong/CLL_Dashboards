"""The deploy archive must contain exactly one database, and a real one.

Covers the failure that put a 4096-byte empty database in the archive beside the
real 110592-byte one: build_deploy_zip.py walks the application folder, and a
cwd-relative default database can be sitting there (Config.DB_PATH defaults to
"./cll_initiatives.db"). Writing both produces a DUPLICATE entry, and the winner
on extraction is order-dependent - so the site could come up against an empty
database. This is the exact "database unreachable" failure the script's own
docstring says has already happened once.
"""
import os
import sqlite3
import subprocess
import sys
import zipfile

import pytest

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
SCRIPTS = os.path.join(R, "scripts")
BUILDER = os.path.join(SCRIPTS, "build_deploy_zip.py")
APP = os.path.join(R, "openspec", "changes", "add-initiative-dashboard-prototype")
STRAY = os.path.join(APP, "cll_initiatives.db")
REAL_DB_SIZE = os.path.getsize(os.path.join(R, "cll_initiatives.db"))


@pytest.fixture
def stray(tmp_path):
    """Recreate the cwd-relative stray database, then clean it up.

    Left behind by any connection that used Config's default path from the app's
    directory. It is gitignored, so on a fresh clone it is ABSENT - which is why
    this test creates it rather than assuming it.
    """
    existed = os.path.exists(STRAY)
    if not existed:
        sqlite3.connect(STRAY).close()
    yield STRAY
    if not existed:
        try:
            os.remove(STRAY)
        except OSError:
            pass


def _build(out):
    p = subprocess.run([sys.executable, BUILDER, str(out)],
                       capture_output=True, text=True)
    return p


def test_the_archive_has_exactly_one_database_entry(tmp_path, stray):
    out = tmp_path / "deploy.zip"
    p = _build(out)
    assert p.returncode == 0, p.stderr

    z = zipfile.ZipFile(out)
    names = z.namelist()
    assert names.count("cll_initiatives.db") == 1, (
        "the archive contains %d cll_initiatives.db entries; extraction order "
        "decides which one the site serves" % names.count("cll_initiatives.db"))


def test_the_archive_database_is_the_real_one_not_the_stray(tmp_path, stray):
    """A duplicate is bad; silently shipping the EMPTY one is worse."""
    out = tmp_path / "deploy.zip"
    _build(out)
    z = zipfile.ZipFile(out)
    entries = [i for i in z.infolist() if i.filename == "cll_initiatives.db"]
    assert len(entries) == 1
    assert entries[0].file_size == REAL_DB_SIZE, (
        "the archived database is %d bytes; the real one is %d - the empty stray "
        "was packaged" % (entries[0].file_size, REAL_DB_SIZE))


def test_the_archive_has_no_duplicate_entries_at_all(tmp_path, stray):
    """Any duplicate is a bug, not just the database one."""
    out = tmp_path / "deploy.zip"
    _build(out)
    names = zipfile.ZipFile(out).namelist()
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, "duplicate archive entries: %s" % dupes


def test_the_archive_contains_the_files_the_site_needs(tmp_path, stray):
    out = tmp_path / "deploy.zip"
    _build(out)
    names = set(zipfile.ZipFile(out).namelist())
    for required in ("app/main.py", "app/oct16_data.py", "app/templates/base.html",
                     "requirements.txt", "cll_initiatives.db"):
        assert required in names, "missing from the archive: %s" % required
