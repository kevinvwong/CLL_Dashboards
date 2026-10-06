"""Dated copies of the SQLite database (task 9.3).

    python scripts/backup.py [--db path] [--dir backups] [--keep 14]

Uses SQLite's online backup API, so a copy taken while the app is serving is
consistent rather than a byte copy of a file mid-write.

**This exists only because the prototype runs on SQLite.** Once the data
moves to Azure SQL, point-in-time restore replaces it and this script is
deleted rather than ported (design.md decision 15). Task 9.3 carries that
note.
"""

import argparse
import datetime as dt
import os
import shutil
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "..", "cll_initiatives.db")
DEFAULT_DIR = os.path.join(HERE, "..", "backups")


def backup(db_path: str, backup_dir: str, keep: int = 14, now=None):
    """Take one dated copy and prune anything past `keep`. Returns the path."""
    now = now or dt.date.today()
    os.makedirs(backup_dir, exist_ok=True)
    target = os.path.join(backup_dir, f"cll_{now:%Y%m%d}.db")

    source = sqlite3.connect(db_path)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()

    prune(backup_dir, keep)
    return target


def prune(backup_dir: str, keep: int = 14):
    """Remove the oldest copies beyond `keep`."""
    copies = sorted(f for f in os.listdir(backup_dir) if f.startswith("cll_") and f.endswith(".db"))
    removed = []
    for name in copies[:-keep] if keep > 0 else copies:
        path = os.path.join(backup_dir, name)
        os.remove(path)
        removed.append(name)
    return removed


def latest(backup_dir: str):
    copies = sorted(f for f in os.listdir(backup_dir) if f.startswith("cll_") and f.endswith(".db"))
    return os.path.join(backup_dir, copies[-1]) if copies else None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Back up the SQLite database.")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--dir", default=DEFAULT_DIR)
    parser.add_argument("--keep", type=int, default=14)
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"No database at {args.db}", file=sys.stderr)
        return 1

    path = backup(args.db, args.dir, args.keep)
    kept = len([f for f in os.listdir(args.dir) if f.endswith(".db")])
    print(f"Wrote {path}  ({kept} of {args.keep} copies kept)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())