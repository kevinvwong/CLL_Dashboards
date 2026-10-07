"""The register seed: counts, owner names, team moves, and reproducibility.

Reads the built cll_initiatives.db. The db is rebuilt from the register by
db/build_db.py, so these assertions describe the seed's effect, not the seed
text. The reproducibility test rebuilds twice and compares hashes.
"""
import hashlib
import os
import re
import sqlite3
import subprocess
import sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(R, "cll_initiatives.db")


def _con():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def test_dean_layer_counts():
    con = _con()
    assert con.execute("SELECT COUNT(*) FROM DeanPriorities").fetchone()[0] == 11
    assert con.execute(
        "SELECT COUNT(*) FROM DeanPriorities WHERE FiscalYear=26").fetchone()[0] == 3
    assert con.execute(
        "SELECT COUNT(*) FROM DeanPriorities WHERE FiscalYear=27").fetchone()[0] == 8
    con.close()


def test_link_counts():
    con = _con()
    assert con.execute("SELECT COUNT(*) FROM MajorInitiativeGoals").fetchone()[0] == 58
    assert con.execute("SELECT COUNT(*) FROM MajorInitiativeDeanLinks").fetchone()[0] == 61
    con.close()


def test_every_major_initiative_has_an_owner():
    con = _con()
    missing = con.execute(
        "SELECT COUNT(*) FROM MajorInitiatives WHERE OwnerID IS NULL").fetchone()[0]
    assert missing == 0
    con.close()


def test_owners_are_real_names():
    con = _con()
    names = {r[0] for r in con.execute("SELECT Name FROM People")}
    assert {"Bill Gaudelli", "Mario Herane", "Tim Jacobbe",
            "Meltem Alemdar", "Elizabeth Smith", "Grace Flavin"} <= names
    con.close()


def test_team_reassignments_landed():
    """The four moved rows are under Learning Ecosystems."""
    con = _con()
    moved = ("Growth Engine Readiness", "Strategic Partnership & Revenue Growth",
             "Geographic Expansion", "Asset Utilization")
    for title in moved:
        team = con.execute(
            "SELECT t.Name FROM MajorInitiatives k JOIN Teams t ON t.TeamID=k.TeamID "
            "WHERE k.Title=?", (title,)).fetchone()
        assert team and team[0] == "Learning Ecosystems", title
    con.close()


def test_reworded_titles_landed():
    con = _con()
    got = {r[0]: r[1] for r in con.execute(
        "SELECT Code, Title FROM MajorInitiatives")}
    assert got["5-09"] == "Build coursework as reusable learning experiences"
    assert got["5-05"] == ("Empower faculty to engage in innovative program "
                           "development and align work functions")
    con.close()


def test_learning_futures_co_owner():
    """The register names two co-owners for Learning Futures; the second is held
    in MajorInitiativeCoOwners, not lost."""
    con = _con()
    co = con.execute(
        "SELECT COUNT(*) FROM MajorInitiativeCoOwners co "
        "JOIN People p ON p.PersonID=co.PersonID WHERE p.Name='Grace Flavin'"
    ).fetchone()[0]
    assert co == 6
    con.close()


def test_percent_scaling():
    con = _con()
    got = {r[0]: r[1] for r in con.execute(
        "SELECT Title, PercentComplete FROM DeanPriorities")}
    assert got["OMS AI"] == 50          # register 0.5
    assert got["Strategy '35 Develop"] == 100   # register 1
    assert got["Financial & Labor Optimization"] == 0
    con.close()


def test_seed_has_no_clock_default():
    """The generated seed must not depend on date('now')/datetime('now')."""
    sql = open(os.path.join(R, "db", "seed_register.sql"), encoding="utf-8").read()
    assert not re.search(r"(date|datetime)\('now'\)", sql)


def test_build_is_reproducible():
    """Two builds from the same seed produce byte-identical databases."""
    def _hash():
        subprocess.run([sys.executable, os.path.join(R, "db", "build_db.py")],
                       check=True, capture_output=True)
        return hashlib.sha256(open(DB, "rb").read()).hexdigest()

    assert _hash() == _hash()
