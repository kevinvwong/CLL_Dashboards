"""Build cll_initiatives.db from schema.sql and seed_sample.sql.
Usage:  python3 build_db.py            (schema + sample data)
        python3 build_db.py --empty    (schema only)
"""
import sqlite3, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "cll_initiatives.db")
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")
# encoding="utf-8" is REQUIRED, not cosmetic. Without it Python decodes the files
# as the platform default (cp1252 on Windows), so a UTF-8 curly apostrophe in the
# canonical goal wording is misread and re-encoded into the database as mojibake:
#   expected  world's
#   stored    worldâ€™s
# The goal wording comes from the Strategy 2035 deck and contains U+2019 and
# U+2013, so this corrupted the canonical text the goal-data-correctness tests
# exist to protect. Fixed 2026-10-07.
con.executescript(open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read())
if "--empty" not in sys.argv:
    con.executescript(open(os.path.join(HERE, "seed_sample.sql"), encoding="utf-8").read())
    # The organizational layer (teams, source areas, 29 Team Initiatives, and the four
    # governed priority fields) generated from the Dean's prototype. Loaded
    # after the sample seed because it updates Priorities by name.
    team_layer = os.path.join(HERE, "seed_team_layer.sql")
    if os.path.exists(team_layer):
        con.executescript(open(team_layer, encoding="utf-8").read())
    # The canon workbook's stable keys, exact titles, and the MI -> Goal edge.
    # Loaded after the team layer because it updates TeamInitiatives by Code.
    canon = os.path.join(HERE, "seed_canon_links.sql")
    if os.path.exists(canon):
        con.executescript(open(canon, encoding="utf-8").read())
    # The register (2026-10-07 canon): named owners, descriptions, team moves,
    # the Goal and Priority edges, and the Dean Initiatives layer. Loaded last,
    # because it updates TeamInitiatives and People set by earlier seeds.
    register = os.path.join(HERE, "seed_register.sql")
    if os.path.exists(register):
        con.executescript(open(register, encoding="utf-8").read())
    # The Milestones model, the priority outcome state and the provenance row
    # (enhancement work, 2026-10-07). Loaded LAST: it updates Priorities by Code
    # and inserts Milestones whose PriorityCode references them.
    milestones = os.path.join(HERE, "seed_milestones.sql")
    if os.path.exists(milestones):
        con.executescript(open(milestones, encoding="utf-8").read())
con.commit()
for t in ["Goals","Priorities","People","Teams","SourceAreas",
          "TeamInitiatives","TeamInitiativePriorities","TeamInitiativeGoals",
          "DeanInitiatives","TeamInitiativeDeanLinks","TeamInitiativeCoOwners",
          "TeamInitiativeUpdates","Milestones","AppMeta","AuditLog"]:
    print(f"{t:22} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>4} rows")
issues = con.execute("SELECT Code, Issue FROM vw_DataChecks").fetchall()
print(f"\nData checks: {len(issues)} issue(s)")
for c, i in issues:
    print(f"  {c}: {i}")
con.close()
print(f"\nBuilt {DB}")
