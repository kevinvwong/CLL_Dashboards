"""Apply the Rev2 T-SQL port to the Azure SQL target, batch by batch on GO.

    python db/mssql/apply.py            # apply 001..007 in order
    python db/mssql/apply.py --check    # report which objects exist, apply nothing

`GO` is a client-side batch separator, not a server statement, so a naive
executescript fails. Each batch runs on its own; the scripts are idempotent
(IF OBJECT_ID ... IS NULL / CREATE OR ALTER), so re-running is safe.

Credentials come from the REV2_CREDS environment variable, or the default
temp file. They are never printed.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CREDS = os.path.join(os.environ.get("TEMP", "/tmp"), "opencode", "rev2sql.txt")
# Order matters: tables, constraints, cardinality, conformance, canonical
# protection, read models, integrity report; the app-layer additions last (they
# only reference tables 001 created).
ORDER = [
    "001_rev2_tables.sql",
    "002_constraints.sql",
    "003_cardinality.sql",
    "004_conformance_fixes.sql",
    "005_canonical_protection.sql",
    "006_read_models.sql",
    "007_integrity_report.sql",
    "008_app_layer.sql",
]


def _creds():
    path = os.environ.get("REV2_CREDS", DEFAULT_CREDS)
    d = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                d[k.strip()] = v.strip()
    return d


def _batches(sql):
    parts = re.split(r"^\s*GO\s*$", sql, flags=re.I | re.M)
    return parts


def apply(files):
    import pymssql

    c = _creds()
    conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                           database=c["DB"], login_timeout=90, timeout=120)
    conn.autocommit(True)
    cur = conn.cursor()
    total_fail = 0
    for name in files:
        path = os.path.join(HERE, name)
        sql = open(path, encoding="utf-8").read()
        ok = fail = 0
        for i, part in enumerate(_batches(sql), 1):
            body = "\n".join(l for l in part.split("\n") if not l.strip().startswith("--"))
            if not body.strip():
                continue
            try:
                cur.execute(body)
                while cur.nextset():
                    pass
                ok += 1
            except Exception as exc:
                fail += 1
                print("  FAIL %s batch %d: %s" % (name, i, str(exc).replace("\n", " ")[:200]))
        total_fail += fail
        print("%-32s batches ok=%d fail=%d" % (name, ok, fail))
    conn.close()
    return 1 if total_fail else 0


def check():
    import pymssql

    c = _creds()
    conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                           database=c["DB"], login_timeout=90, timeout=120)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.VIEWS")
    views = cur.fetchone()[0]
    print("tables=%s views=%s" % (tables, views))
    conn.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report object counts, apply nothing")
    ap.add_argument("files", nargs="*", help="SQL files to apply, relative to this dir (default: 001..007)")
    args = ap.parse_args(argv)
    if args.check:
        return check()
    files = args.files
    if not files:
        files = ORDER
    # A path may be given relative to the repo root; resolve against HERE then root.
    resolved = []
    for f in files:
        p = f if os.path.isabs(f) else (f if os.path.exists(os.path.join(HERE, f))
                                        else os.path.join(HERE, "..", f))
        resolved.append(p)
    return apply(resolved)


if __name__ == "__main__":
    raise SystemExit(main())
