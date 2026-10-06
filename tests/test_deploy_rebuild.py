"""The deploy archive carries a complete rebuild path.

Found 2026-10-06: the schema gained Teams/SourceAreas/MajorInitiatives but the archive
shipped only seed_sample.sql, so a rebuild from the archive produced the tables
with no rows. The deployed db file was fine - only the rebuild path was broken -
which is why nothing caught it. This guards the rebuild path directly.
"""
import os
import subprocess
import sys
import zipfile

import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(R, "scripts", "build_deploy_zip.py")
APP = os.path.join(R, "app")
STRAY = os.path.join(APP, "cll_initiatives.db")


@pytest.fixture
def stray():
    existed = os.path.exists(STRAY)
    if not existed:
        import sqlite3
        sqlite3.connect(STRAY).close()
    yield STRAY
    if not existed:
        try:
            os.remove(STRAY)
        except OSError:
            pass


def test_the_archive_ships_every_seed_the_schema_needs(tmp_path, stray):
    """Every seed file the schema relies on must be in the archive.

    seed_sample.sql populates the base tables; seed_team_layer.sql populates the
    organizational layer the schema added. Both are needed for a rebuild.
    """
    out = tmp_path / "deploy.zip"
    p = subprocess.run([sys.executable, BUILDER, str(out)],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    names = set(zipfile.ZipFile(out).namelist())
    for required in ("db/schema.sql", "db/seed_sample.sql", "db/seed_team_layer.sql"):
        assert required in names, "the archive is missing %s" % required


def test_a_rebuild_from_the_archive_reproduces_the_team_layer(tmp_path, stray):
    """Build a database from the archive's own schema and seeds.

    This is the strongest form: it proves the shipped files are sufficient to
    reconstruct the data, not merely present. If seed_team_layer.sql were
    dropped again, the MajorInitiatives count would be zero and this fails.
    """
    import sqlite3

    out = tmp_path / "deploy.zip"
    subprocess.run([sys.executable, BUILDER, str(out)], check=True,
                   capture_output=True, text=True)
    extract = tmp_path / "site"
    zipfile.ZipFile(out).extractall(extract)

    rebuilt = tmp_path / "rebuilt.db"
    conn = sqlite3.connect(str(rebuilt))
    try:
        conn.executescript(open(os.path.join(extract, "db", "schema.sql"),
                                encoding="utf-8").read())
        conn.executescript(open(os.path.join(extract, "db", "seed_sample.sql"),
                                encoding="utf-8").read())
        conn.executescript(open(os.path.join(extract, "db", "seed_team_layer.sql"),
                                encoding="utf-8").read())
        conn.commit()
        counts = {
            t: conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
            for t in ("Goals", "Priorities", "Initiatives", "Teams",
                      "SourceAreas", "MajorInitiatives", "MajorInitiativePriorities")
        }
    finally:
        conn.close()

    assert counts["Teams"] == 4, counts
    assert counts["SourceAreas"] == 5, counts
    assert counts["MajorInitiatives"] == 29, counts
    assert counts["MajorInitiativePriorities"] == 51, counts
    assert counts["Initiatives"] == 22, counts
