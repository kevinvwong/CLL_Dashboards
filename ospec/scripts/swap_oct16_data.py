"""Regenerate the October 16 page for a confirmed data swap, with a dry run.

    python scripts/swap_oct16_data.py --owners owners.json --dry-run
    python scripts/swap_oct16_data.py --owners owners.json

The dry run reports every difference the swap would make and changes NOTHING. The
real run backs the live database up first, then regenerates the module.

Why this exists rather than just running build_oct16_data.py: a swap changes what
the Dean's page says, and the procedure has to be reversible. The dry run is how
you find out what it will do before it does it, and the backup is what makes the
data half of a rollback possible. See docs/DEPLOY.md for the deploy half.

Task 4.1-4.4 of launch-initiatives-dashboard-live.
"""

import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.dirname(HERE)
APP = os.path.join(SPEC, "openspec", "changes", "add-initiative-dashboard-prototype")
MODULE = os.path.join(APP, "app", "oct16_data.py")
GENERATOR = os.path.join(HERE, "build_oct16_data.py")
BACKUP = os.path.join(HERE, "backup.py")
DB = os.path.join(SPEC, "cll_initiatives.db")


def load(path):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def describe(current, incoming):
    """Every difference the swap would make, in words."""
    lines = []

    if current.CONFIRMED != incoming.CONFIRMED:
        lines.append("  marker         : %r -> %r"
                     % (current.data_status(), incoming.data_status()))
    elif current.data_status() != incoming.data_status():
        lines.append("  marker         : %r -> %r"
                     % (current.data_status(), incoming.data_status()))

    cur = {o["id"]: o for o in current.OUTCOMES}
    inc = {o["id"]: o for o in incoming.OUTCOMES}

    # Outcomes appearing or disappearing.
    for oid in sorted(set(inc) - set(cur)):
        lines.append("  + %s added" % oid)
    for oid in sorted(set(cur) - set(inc)):
        lines.append("  - %s removed" % oid)

    for oid in sorted(set(cur) & set(inc)):
        a, b = cur[oid], inc[oid]

        def owner(mod, o):
            return mod.owner_label(o["owner"])

        if owner(current, a) != owner(incoming, b):
            lines.append("  %s owner      : %r -> %r" % (oid, owner(current, a), owner(incoming, b)))
        if a["updated"] != b["updated"]:
            lines.append("  %s updated    : %r -> %r" % (oid, a["updated"], b["updated"]))
        if (a["reached"], a["planned"]) != (b["reached"], b["planned"]):
            lines.append("  %s milestones : %d/%d -> %d/%d"
                         % (oid, a["reached"], a["planned"], b["reached"], b["planned"]))
        if a["status"] != b["status"]:
            lines.append("  %s status     : %r -> %r" % (oid, a["status"], b["status"]))
        am = dict(a["milestones"])
        bm = dict(b["milestones"])
        for name in sorted(set(am) | set(bm)):
            if am.get(name) != bm.get(name):
                lines.append("  %s milestone %r: %r -> %r"
                             % (oid, name, am.get(name), bm.get(name)))

    # Layout must not move. Asserted here as well as in the tests, because the dry
    # run is what a person reads before approving the swap.
    if len(current.DATA_REQUIREMENTS) != len(incoming.DATA_REQUIREMENTS):
        lines.append("  WARNING: the data-requirements table changed size: %d -> %d"
                     % (len(current.DATA_REQUIREMENTS), len(incoming.DATA_REQUIREMENTS)))
    if [s[1] for s in current.SCOPE] != [s[1] for s in incoming.SCOPE]:
        lines.append("  WARNING: the scope figures changed: %s -> %s"
                     % ([s[1] for s in current.SCOPE], [s[1] for s in incoming.SCOPE]))

    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owners", required=True, help="JSON file of confirmed owners")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change and change nothing")
    args = ap.parse_args()

    if not os.path.exists(args.owners):
        raise SystemExit("owners file not found: %s" % args.owners)
    owners_data = json.load(open(args.owners, encoding="utf-8-sig"))
    if not owners_data:
        raise SystemExit("owners file is empty; refusing to swap")

    # Generate to a temp path first, always, so nothing is written until the diff
    # has been read.
    import tempfile
    staged = os.path.join(tempfile.mkdtemp(), "oct16_data.py")
    p = subprocess.run(
        [sys.executable, GENERATOR, "--owners", args.owners, "--out", staged],
        capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("generator failed:\n" + p.stderr)

    current = load(MODULE)
    incoming = load(staged)

    print("current : %s" % current.data_status())
    print("incoming: %s" % incoming.data_status())
    print()

    diffs = describe(current, incoming)
    if not diffs:
        print("No differences. Nothing to swap.")
        return

    print("The swap would make these changes:")
    for line in diffs:
        print(line)

    if args.dry_run:
        print()
        print("DRY RUN: nothing was written.")
        return

    # Back the database up BEFORE writing the module, so the data half of a
    # rollback is possible. The filename is printed because the runbook needs it.
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_dir = os.path.join(SPEC, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    target = os.path.join(backup_dir, "cll_preswap_%s.db" % stamp)
    src = sqlite_connect(DB)
    try:
        dst = sqlite_connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    print()
    print("Backed up before swap: %s" % target)

    shutil.copy2(staged, MODULE)
    after = load(MODULE)
    print("Wrote %s" % MODULE)
    print("  marker now: %s" % after.data_status())
    print()
    print("To roll back this swap: restore %s over %s and redeploy."
          % (target, DB))


def sqlite_connect(path):
    import sqlite3
    return sqlite3.connect(path)


if __name__ == "__main__":
    main()
