"""Link a Clerk user to a Dashboard person (the first-admin bootstrap).

    python scripts/link_clerk_user.py <clerk_user_id> <person_id>

The Clerk user id looks like `user_...` (find it in the Clerk dashboard, or
`clerk users list --app <app_id>`). The person id is the row in this app's
`People` table (e.g. the dashboard admin).

This is the one step an admin cannot do in the app, because the admin is the
person being linked: until the link exists they see the "not linked" page. Run
it once per person, per environment. It is not a seed: a Clerk user id is
per-person and per-environment, so it does not belong in the committed sample
database.
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "..", "cll_initiatives.db")


def link(db_path: str, clerk_user_id: str, person_id: int) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT Name FROM People WHERE PersonID = ?", (person_id,)).fetchone()
        if row is None:
            print("no such person: %s" % person_id, file=sys.stderr)
            return 1
        conn.execute("UPDATE People SET ClerkUserID = ? WHERE PersonID = ?",
                     (clerk_user_id, person_id))
        conn.commit()
        print("linked Clerk %s -> person %s (%s)" % (clerk_user_id, person_id, row[0]))
    except sqlite3.IntegrityError:
        print("that Clerk user is already linked to another person", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


def main(argv=None):
    args = (argv if argv is not None else sys.argv)[1:]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    db = os.environ.get("DB_PATH", DEFAULT_DB)
    return link(db, args[0], int(args[1]))


if __name__ == "__main__":
    raise SystemExit(main())
