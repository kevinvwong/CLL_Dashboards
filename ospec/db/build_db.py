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
con.executescript(open(os.path.join(HERE, "schema.sql")).read())
if "--empty" not in sys.argv:
    con.executescript(open(os.path.join(HERE, "seed_sample.sql")).read())
con.commit()
for t in ["Goals","Priorities","People","Initiatives","InitiativeGoals",
          "InitiativePriorities","InitiativeLinks","ProgressUpdates"]:
    print(f"{t:22} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>4} rows")
issues = con.execute("SELECT Code, Issue FROM vw_DataChecks").fetchall()
print(f"\nData checks: {len(issues)} issue(s)")
for c, i in issues:
    print(f"  {c}: {i}")
con.close()
print(f"\nBuilt {DB}")
