"""Generate docs/ops/PROGRESS_LOG.md from git history.

    python scripts/build_progress_log.py            # writes the log
    python scripts/build_progress_log.py --check    # fail if it is stale

The log is written for a NON-TECHNICAL reader: it groups each day's commits under
plain headings ("What we added", "What we fixed", "Behind the scenes") and strips
the engineering shorthand (`feat(schema): ...`) from each line. It never invents
meaning - the words are the commit's own, only re-headed.

It is deterministic: the same history always yields the same file, so `--check`
can prove the committed log is current. It reads only `git log`; it never runs the
app, the tests, or the database.
"""
import argparse
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "ops", "PROGRESS_LOG.md")

#: Conventional-commit type -> the plain heading a non-technical reader sees.
#: Order is the order the headings appear within a day.
SECTIONS = [
    ("What we added",      ("feat",)),
    ("What we fixed",      ("fix",)),
    ("Appearance and design", ("style", "design")),
    ("Behind the scenes",  ("refactor", "chore", "build", "ci", "perf")),
    ("Quality and testing", ("test",)),
    ("Documentation",      ("docs",)),
]
#: Commits with no recognised type land here.
FALLBACK = "More changes"

#: Two thirds of the commits predate the `type: ...` convention, so they have no
#: prefix to classify by. Rather than dump them under one vague heading, classify
#: by the FIRST WORD of the message (a verb such as "Add", "Fix", "Move"). This is
#: a documented transformation of the text, not a judgement about it: the line the
#: reader sees is unchanged, only its heading is chosen.
VERB_SECTIONS = {
    "What we added": ("add", "apply", "build", "create", "incorporate",
                      "prepare", "scaffold", "ship", "stand", "surface"),
    "What we fixed": ("correct", "fix", "free", "harden", "match", "refuse",
                      "reorder", "resolve", "restore"),
    "Appearance and design": ("design", "paint", "restyle", "style"),
    "Behind the scenes": ("archive", "call", "choose", "commit", "cut",
                          "deepen", "derive", "drop", "follow", "move", "read",
                          "record", "relocate", "rename", "replace",
                          "restructure", "retarget", "retire"),
    "Documentation": ("describe", "document", "state", "write"),
}

#: A short, factual glossary. Only terms a reader will actually meet.
GLOSSARY = [
    ("Register", "the official spreadsheet of the College's approved work that "
                 "this dashboard shows"),
    ("Team Initiative", "one of the 29 bodies of work the College will deliver"),
    ("Dean Initiative", "one of the top-level pieces of work owned by the Dean"),
    ("Priority", "one of the six yearly focus areas (the dashboard shows "
                 "'Priority 1', 'Priority 2', ...)"),
    ("Goal", "one of the five Strategy 2035 goals the work aligns to"),
    ("Dashboard", "the web page this log describes"),
    ("Prototype", "an early, non-final version used to agree the design"),
]

#: A leading byte-order mark or stray control char occasionally rides on a
#: commit subject; drop it so the log is clean.
_JUNK = re.compile("^[\ufeff\u200b\ufffd]+")
_PREFIX = re.compile(r"^([a-z]+)(\([^)]*\))?:\s*", re.I)


def _git_log():
    """[(date, short-sha, subject)] oldest first, author dates."""
    out = subprocess.run(
        ["git", "-C", ROOT, "log", "--date=short", "--reverse",
         "--no-merges", "--pretty=format:%ad|%h|%s"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise SystemExit("git log failed: " + out.stderr)
    rows = []
    for line in out.stdout.splitlines():
        if line.count("|") < 2:
            continue
        d, h, s = line.split("|", 2)
        rows.append((d.strip(), h.strip(), _JUNK.sub("", s.strip())))
    return rows


def _section_of(subject):
    """The heading for a subject: by commit type, else by its first word."""
    body = _PREFIX.sub("", subject).strip() or subject
    m = _PREFIX.match(subject)
    if m:
        t = m.group(1).lower()
        for heading, types in SECTIONS:
            if t in types:
                return heading
    first = body.split(" ", 1)[0].strip().strip("'\".,:").lower()
    for heading, verbs in VERB_SECTIONS.items():
        if first in verbs:
            return heading
    return None          # nothing matched -> the fallback heading


def _plain(subject):
    """The line a reader sees: the prefix removed, first letter capitalised."""
    s = _PREFIX.sub("", subject).strip()
    return (s[:1].upper() + s[1:]) if s else subject


def _readable_date(iso):
    import datetime as dt
    d = dt.date.fromisoformat(iso)
    return d.strftime("%A %d %B %Y")  # e.g. "Wednesday 07 October 2026"


def build():
    rows = _git_log()
    by_day = {}
    for date, sha, subject in rows:
        by_day.setdefault(date, []).append((sha, subject))

    L = []
    L.append("# CLL Initiative Dashboard — progress log")
    L.append("")
    L.append("A plain-English record of what changed on the dashboard, day by day. "
             "It is generated from the project's history, so it always matches the "
             "work that actually happened. Newest day first.")
    L.append("")
    L.append("> **Newest first.** This page is produced by "
             "`scripts/build_progress_log.py` — do not edit it by hand; the next "
             "run overwrites it.")
    L.append("")
    L.append("## How to read this")
    L.append("")
    L.append("Each line is one change to the dashboard, under a plain heading. The "
             "wording is the change's own, kept as written so the record stays "
             "accurate; a few lines name technical things (a file, a screen, a "
             "feature) because that is what the change was about. The glossary "
             "below covers the domain words; you do not need the technical ones to "
             "follow the day-to-day story.")
    L.append("")
    L.append("## At a glance")
    L.append("")
    L.append("- **%d** days of work recorded, **%d** changes in total."
             % (len(by_day), len(rows)))
    if by_day:
        newest = max(by_day)
        L.append("- Most recent day: **%s**." % _readable_date(newest))
    # a counted breakdown - no judgement, just how many of each kind
    headings = [h for h, _ in SECTIONS] + list(VERB_SECTIONS) + [FALLBACK]
    order = []
    for h in headings:                      # de-duplicate, keep first-seen order
        if h not in order:
            order.append(h)
    counts = {h: 0 for h in order}
    for _, _, subject in rows:
        counts[_section_of(subject) or FALLBACK] += 1
    parts = ["%d %s" % (n, h.lower()) for h, n in counts.items() if n]
    if parts:
        L.append("- Across all days: " + "; ".join(parts) + ".")
    L.append("")
    L.append("## Words used on this page")
    L.append("")
    for term, meaning in GLOSSARY:
        L.append("- **%s** — %s" % (term, meaning))
    L.append("")
    L.append("---")

    for date in sorted(by_day, reverse=True):
        L.append("")
        L.append("## %s" % _readable_date(date))
        L.append("")
        # keep the declared heading order (type headings, then verb headings,
        # then the fallback), each shown only when it has lines.
        buckets = {h: [] for h in order}
        for sha, subject in by_day[date]:
            head = _section_of(subject) or FALLBACK
            buckets[head].append((sha, subject))
        for heading in order:
            items = buckets.get(heading) or []
            if not items:
                continue
            L.append("**%s**" % heading)
            L.append("")
            for sha, subject in items:
                L.append("- %s" % _plain(subject))
            L.append("")
    L.append("---")
    L.append("")
    L.append("_Generated from git history. Each line is one change; the wording is "
             "the change's own, only grouped and simplified._")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate the progress log from git.")
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed log differs from a fresh build")
    args = ap.parse_args(argv)

    text = build()
    if args.check:
        current = io.open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("PROGRESS_LOG.md is STALE; re-run without --check")
            return 1
        print("PROGRESS_LOG.md is current")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
