"""Generate db/seed_milestone_clauses.sql: one milestone per semicolon-delimited
clause of the register's column F, weighted for the rollup up to the initiative.

    python db/build_milestone_clauses_seed.py           # writes the seed
    python db/build_milestone_clauses_seed.py --check   # fail if the output differs

WHAT THIS REPLACES
------------------
The previous milestone seed was 18 MOCK rows keyed to Priorities, carried from a
wireframe. Its own docstring said "the real milestone content does not exist yet".
That was true on 2026-10-07 and is false now: the real content is column F of the
register, 84 clauses across all 29 rows. The mock rows are gone.

THE SOURCE
----------
"Initiative Dashboard Register.xlsx", sheet "Team KPI Register", column F,
header row 4: "FY2027 Target / Achievement Marks". One cell per register row,
2-5 semicolon-delimited clauses. The clause text is reproduced VERBATIM - the
board's own wording is the atom being reported on, and paraphrasing it here would
make the seed disagree with the register in a way nothing would catch.

THE WEIGHTS ARE INFERRED. THE REGISTER SUPPLIES NONE.
----------------------------------------------------
Column G ("KPI Status") is per-ROW, not per-clause, so the register carries 84
targets and zero per-clause achievement values. A rollup needs weights that do
not exist, so they are derived from two signals the register's own text provides
and the derivation is recorded on every row:

    prominence   clause 1 of a cell is that initiative's headline commitment (1.0)
                later clauses are supporting workstreams (0.5)
    hardness     a numeral that survives reference-stripping is a committed
                magnitude (1.00); a gate verb without one is softer (0.85);
                neither is directional (0.60)

    weight = prominence * hardness, normalised WITHIN the initiative

Reference-stripping matters more than it looks. A naive "contains a digit" test
scores "B2B strategy launched" as quantified, because B2B contains a 2; it also
scores every "...by Q1" as quantified, because Q1 contains a 1. The numerals that
are REFERENCES rather than commitments - quarters, fiscal years, bare years,
product codes, version numbers - are removed before the test. A second attempt
that required the numeral to sit directly beside its unit noun then scored "More
than 1,000 approved objects" as vague, because "approved" sits between them. Both
were caught only by reading the clauses; that is why WeightBasis is stored on the
row instead of being recomputed at read time.

The 12 soft clauses are KEPT and they COUNT - excluding them would quietly
redefine the attainment denominator - but they are flagged NeedsRewrite, because
"personalized journey" cannot honestly be marked Met or Missed.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seed_milestone_clauses.sql")
WORKBOOK = os.environ.get(
    "CLL_REGISTER_XLSX",
    os.path.join(os.path.expanduser("~"), "Downloads",
                 "Initiative Dashboard Register.xlsx"))

#: The plan year this seed describes. Team Initiative codes recur per year, so the
#: milestone's identity is (PlanYear, Code) and not the code alone.
PLAN_YEAR = 2027

#: Numerals that REFERENCE something rather than committing to a magnitude.
REFERENCE_NOISE = [
    re.compile(r"\bQ[1-4]\b", re.I),           # "...by Q1"
    re.compile(r"\bFY\s?\d{2,4}\b", re.I),     # "FY2027"
    re.compile(r"\b(?:19|20)\d{2}\b"),         # bare years: "Strategy 2035"
    re.compile(r"\bB\d[B0-9]*\b"),             # "B2B", "B2C"
    re.compile(r"\b[A-Z][A-Za-z]*\s?\d+\.\d+\b"),  # "Infinity 2.0"
]

#: A gate verb is a dated decision rather than a running activity. Checked against
#: the ORIGINAL text, not the stripped one, so "by Q1" still reads as a gate.
GATE = re.compile(r"\b(approve|launch|establish|complete|instrument|publish|"
                  r"orient|route|align|document|review|map|capture|implement)\b",
                  re.I)

QUARTER = re.compile(r"\bby Q([1-4])\b", re.I)

#: MEASURE IS DELIBERATELY NOT EXTRACTED. Four regex formulations were tried and
#: every one produced junk: the noun group either landed before the numeral
#: ("More than", "at least", "Infinity") or swallowed the head of the following
#: clause ("faculty collaborators from", "qualified and engaged"), and one variant
#: even dropped the leading character ("pproved objects").
#:
#: The register's column F is PROSE, not a structured record - it packs a measure,
#: a threshold, an actor and an event into one sentence. A clause like "Engage at
#: least 25 faculty collaborators from at least 6 colleges" names two thresholds,
#: two nouns and a condition, and no regex settles which noun is THE measure.
#:
#: So the column exists and stays NULL. A column of plausible-looking garbage is
#: worse than an empty one, because every downstream reader assumes it was filled
#: by someone who knew. TargetQuarter IS extracted, because "by Q1" is an
#: unambiguous, low-entropy fact; Measure is not, and pretending otherwise would be
#: the same dishonesty the rest of this seed refuses.


def classify(text):
    """-> (hardness, tag, quarter, measure).

    measure is always None: see the note above _MEASURE. Kept in the
    return shape so the seed columns and the schema columns stay aligned.
    """
    stripped = text
    for pattern in REFERENCE_NOISE:
        stripped = pattern.sub(" ", stripped)
    if re.search(r"\d", stripped):
        tag = "quant"
        hardness = 1.00
    elif GATE.search(text):
        tag = "gate"
        hardness = 0.85
    else:
        tag = "soft"
        hardness = 0.60
    q = QUARTER.search(text)
    return hardness, tag, (int(q.group(1)) if q else None), None


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def sq(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def read_clauses(path=WORKBOOK):
    """-> [(code, title, [(name, order, weight, basis, quarter, measure, rewrite)])]"""
    from openpyxl import load_workbook
    sys.path.insert(0, HERE)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_brs", os.path.join(HERE, "build_register_seed.py"))
    brs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(brs)

    import sqlite3
    con = sqlite3.connect(os.path.join(HERE, "..", "cll_initiatives.db"))
    committed = {norm(t): c for _m, t, c in
                 con.execute("SELECT MIId, Title, Code FROM TeamInitiatives")}
    con.close()

    wb = load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["Team KPI Register"].iter_rows(values_only=True))
    data = [r for r in rows[4:] if r and r[0] and str(r[0]).strip()]
    team = [r for r in data if not str(r[0]).strip().startswith("Dean")]

    out, unmatched = [], []
    for r in team:
        key = norm(r[2])
        code = committed.get(key) or committed.get(norm(brs.RENAMED.get(key, "")))
        if code is None:
            unmatched.append(str(r[2]))
            continue
        clauses = [c.strip() for c in str(r[5] or "").split(";") if c.strip()]
        classified = [classify(c) for c in clauses]
        raw = [(1.0 if i == 0 else 0.5) * c[0] for i, c in enumerate(classified)]
        total = sum(raw)
        made = []
        for i, (name, cls) in enumerate(zip(clauses, classified), start=1):
            hardness, tag, quarter, measure = cls
            basis = ("headline" if i == 1 else "support") + "-" + tag
            made.append({
                "name": name, "order": i, "weight": raw[i - 1] / total,
                "basis": basis, "quarter": quarter, "measure": measure,
                "rewrite": 1 if tag == "soft" else 0,
            })
        out.append((code, str(r[2]).strip(), made))
    if unmatched:
        raise SystemExit("UNMAPPED register rows: %r" % unmatched)
    return out


def build(path=WORKBOOK):
    data = read_clauses(path)
    L = []
    L.append("-- GENERATED by db/build_milestone_clauses_seed.py. Do not hand-edit.")
    L.append("--")
    L.append("-- One milestone per semicolon-delimited clause of the register's column F,")
    L.append("-- \"FY2027 Target / Achievement Marks\". 84 clauses across 29 initiatives.")
    L.append("-- Clause text is VERBATIM from the register.")
    L.append("--")
    L.append("-- WeightBasis records how each weight was derived and WeightSource is")
    L.append("-- 'inferred' throughout: no human has confirmed these yet. See the")
    L.append("-- generator's docstring. NeedsRewrite flags the 12 clauses that are not")
    L.append("-- checkable events by the schema's own definition.")
    L.append("")
    L.append("DELETE FROM Milestones;")
    L.append("")
    total = 0
    for code, title, made in data:
        L.append("-- %s  %s" % (code, title))
        L.append("INSERT INTO Milestones")
        L.append("    (TeamInitiativeID, PlanYear, SortOrder, Name, Measure,")
        L.append("     TargetQuarter, Weight, WeightBasis, WeightSource, NeedsRewrite)")
        L.append("VALUES")
        pid = ("(SELECT TeamInitiativeID FROM TeamInitiatives"
               " WHERE Code=%s AND PlanYear=%d)" % (sq(code), PLAN_YEAR))
        rows = []
        for m in made:
            # TargetQuarter must be emitted as an INTEGER, not a quoted string.
            # SQLite orders TEXT above INTEGER, so the CHECK
            # (TargetQuarter BETWEEN 1 AND 4) evaluates FALSE for '1' and the
            # INSERT is rejected. sq() is right for text columns and wrong here.
            rows.append(
                "  (%s, %d, %d, %s, %s, %s, %.10f, '%s', 'inferred', %d)" % (
                    pid, PLAN_YEAR, m["order"], sq(m["name"]), sq(m["measure"]),
                    ("NULL" if m["quarter"] is None else str(int(m["quarter"]))),
                    m["weight"], m["basis"], m["rewrite"]))
            total += 1
        L.append(",\n".join(rows) + ";")
        L.append("")
    return "\n".join(L), total, len(data)


def main():
    body, total, n_initiatives = build()
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != body:
            sys.stderr.write("STALE: %s differs from the generator\n" % OUT)
            return 1
        print("current")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("wrote %s: %d milestones across %d initiatives" % (OUT, total, n_initiatives))
    return 0


if __name__ == "__main__":
    sys.exit(main())
