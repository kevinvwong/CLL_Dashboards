"""Write db/local_overlay.sql from the current database, so a rebuild keeps
environment-specific data (the Clerk user ids that link an SSO identity to a
People row).

    python scripts/write_local_overlay.py

Run this AFTER linking Clerk users (scripts/link_clerk_user.py) so that the next
`python db/build_db.py` does not wipe the links. The overlay is gitignored.
"""
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("DB_PATH", os.path.join(HERE, "..", "cll_initiatives.db"))
OUT = os.path.join(HERE, "..", "db", "local_overlay.sql")

HEADER = """-- LOCAL overlay (gitignored). Applied by build_db.py after every seed.
-- Environment-specific data that must not be committed.
-- Regenerate with: python scripts/write_local_overlay.py
-- The Clerk user ids an SSO identity maps to (People.ClerkUserID).
"""


def main():
    conn = sqlite3.connect(DB)
    try:
        rows = list(conn.execute(
            "SELECT PersonID, ClerkUserID FROM People "
            "WHERE ClerkUserID IS NOT NULL ORDER BY PersonID"))
    finally:
        conn.close()
    lines = [HEADER]
    for pid, cid in rows:
        lines.append("UPDATE People SET ClerkUserID=%r WHERE PersonID=%d;" % (cid, pid))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s (%d Clerk links)" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
