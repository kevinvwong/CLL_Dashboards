"""Build app/oct16_data.py, the October 16 page's content module.

    python scripts/build_oct16_data.py                       # illustrative
    python scripts/build_oct16_data.py --owners owners.json  # confirmed

Without --owners the module is written with CONFIRMED = False and every owner
unset, which is the committed state: illustrative figures, no owner named.

With --owners it writes CONFIRMED = True and the named owners, so a swap to
confirmed data clears the illustrative marker BY ITSELF. That is the point of
deriving the marker from the data rather than setting it by hand - see the
`confirmed-data` spec. Nothing else has to be changed at swap time.

The owners file is JSON:

    {
      "P01": {"owner": "Some Person", "updated": "2026-10-13"},
      "P02": {"owner": "[owner withheld]"}
    }

`"[owner withheld]"` is a deliberate value: it means an owner exists but their
name is not placed on this service. It renders as a marked placeholder and is
never treated as a confirmed owner.

Provenance of the content: the outcome names, targets and the data-requirements
table come from the wireframes and `Oct16_Wireframe_Data_Lists.xlsx`. This script
does not invent values; without --owners it writes only what those sources state.
"""

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.dirname(HERE)  # the repo root
APP = os.path.join(SPEC, "app")
OUT = os.path.join(APP, "oct16_data.py")

# The wireframe's own workbook, which the page cites as the source of its
# data-requirements table. Read rather than retyped, so the page and the workbook
# cannot disagree. Downloaded alongside the wireframes; not in the repo.
WORKBOOK = os.path.join(os.path.expanduser("~"), "Downloads",
                        "Oct16_Wireframe_Data_Lists.xlsx")

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))


def read_requirements(workbook: str = WORKBOOK):
    """The 'Option A Data' rows: the 19-element data-requirements table.

    Missing workbook is not fatal - the page then omits the table rather than
    shipping invented rows - but it is reported, because a silently absent table
    looks like a design choice.
    """
    if not os.path.exists(workbook):
        print("  WARNING: %s not found; DATA_REQUIREMENTS will be empty" % workbook,
              file=sys.stderr)
        return []

    z = zipfile.ZipFile(workbook)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))

    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid2t = {r.get("Id"): r.get("Target") for r in rels}
    sheet_path = None
    for sh in wb.iter(NS + "sheet"):
        if sh.get("name") == "Option A Data":
            tgt = rid2t.get(sh.get(RNS + "id"), "")
            sheet_path = "xl/" + tgt.lstrip("/").replace("xl/", "", 1)
            break
    if not sheet_path or sheet_path not in z.namelist():
        print("  WARNING: sheet 'Option A Data' not found", file=sys.stderr)
        return []

    # This workbook writes unprefixed tags (<row>); the source package wrote
    # <x:row>. Tolerate both, or the sheet silently reads as empty.
    raw = z.read(sheet_path).decode("utf-8", "replace")
    rows = []
    for rm in re.finditer(r"<(?:x:)?row\b[^>]*>(.*?)</(?:x:)?row>", raw, re.S):
        cells = {}
        for cm in re.finditer(
                r'<(?:x:)?c\b r="([A-Z]+)\d+"([^>]*)>(.*?)</(?:x:)?c>', rm.group(1), re.S):
            col, attrs, body = cm.group(1), cm.group(2), cm.group(3)
            t = re.search(r't="(\w+)"', attrs)
            t = t.group(1) if t else "n"
            val = ""
            v = re.search(r"<(?:x:)?v>(.*?)</(?:x:)?v>", body, re.S)
            if v:
                val = v.group(1)
                if t == "s":
                    try:
                        val = shared[int(val)]
                    except (ValueError, IndexError):
                        pass
            elif t == "str":
                m = re.search(r"<(?:x:)?t[^>]*>(.*?)</(?:x:)?t>", body, re.S)
                val = m.group(1) if m else ""
            if val.strip():
                cells[col] = _unescape(val.strip())
        if cells:
            rows.append(cells)

    out = []
    for r in rows[1:]:                      # skip the header row
        if not r.get("A"):
            continue
        out.append({
            "id": r.get("A", ""),
            "section": r.get("B", ""),
            "element": r.get("C", ""),
            "definition": r.get("D", ""),
            "example": r.get("E", ""),
            "volume": r.get("F", ""),
            "source": r.get("G", ""),
            "provided_by": r.get("H", ""),
            "available": r.get("I", ""),
            "how": r.get("J", ""),
            "needed": r.get("K", ""),
        })
    return out

# The outcome scaffold. Milestones and targets are the wireframes' illustrative
# values; the owners come from --owners or are left unset.
OUTCOMES = [
    ("P01", "One Shared Identity", "On track", 1, 4,
     "All 4 teams adopt the message architecture by Q2; 90% of assets aligned by Q4",
     [("Message architecture approved", "Met"),
      ("Teams adopted (1 of 4)", "In progress"),
      ("First asset audit", "Not started")]),
    ("P02", "Champion Innovation", "On track", 2, 5,
     "6 priority pilots; 3 scale, adapt or stop decisions",
     [("RDI baseline complete", "Met"),
      ("Innovation call launched", "Met"),
      ("First stage-gate decisions", "Due Dec")]),
    ("P03", "Integrated Portfolio & Pathways", "At risk", 1, 4,
     "2 badged pathways; all new programs mapped; one approval workflow by Q2",
     [("Unified approval process", "In progress"),
      ("First badged pathway", "In progress"),
      ("Mapping rule approved", "Met")]),
    ("P04", "Quality at Scale", "At risk", 0, 3,
     "20% content reuse; 28-day builds; quality standard on all scaled offerings",
     [("Quality standard approved", "Not started"),
      ("Reuse baseline", "In progress"),
      ("Build-time baseline", "Not started")]),
    ("P05", "Data-Informed Action", "On track", 2, 4,
     "5 dashboards by Q2; every KPI owned; monthly reviews",
     [("KPI definitions drafted", "Met"),
      # This milestone IS the dashboard. It read "This decision" while the option
      # was pending; now that A is chosen it is In progress, not Met - the
      # dashboard is not delivered until 2026-10-16.
      ("College dashboard", "In progress"),
      ("Owners named", "Not started")]),
    ("P06", "Culture & Learning", "On track", 1, 3,
     "Operating models tested; quarterly learning reviews; 90% of commitments current",
     [("Target structure approved", "Confirm"),
      ("Q1 learning reviews", "In progress"),
      ("Operating model template", "Met")]),
]

SCOPE = [
    ("Data elements", "19", "on this wireframe"),
    ("Required for Oct 16", "16", "none deferred"),
    ("In hand now", "8 of 16", "2 partial, 6 not collected"),
    ("Items to collect", "20\u201330", "milestones, status from owners"),
    ("People to ask", "4", "team leads, for owners, dates and status"),
    ("Realistic by Oct 16?", "Yes", "if scoped down"),
]

TRADE_OFFS = [
    (True, "Uses the Dean's own framing from the Blueprint"),
    (True, "Milestone counts are honest: no invented composite scores"),
    (True, "Grows into the full KPI dashboard later"),
    (False, "Does not match the 2026 priorities presented in May"),
    (False, "Needs about 25 milestone updates from owners in one week"),
]


def build(owners_path: str | None, out_path: str = OUT) -> str:
    owners = {}
    if owners_path:
        if not os.path.exists(owners_path):
            raise SystemExit("owners file not found: %s" % owners_path)
        # utf-8-sig, not utf-8: PowerShell's `-Encoding utf8` writes a BOM, and
        # json.load rejects it with "Unexpected UTF-8 BOM" - a failure about the
        # file's first byte, not about its contents. utf-8-sig strips a BOM if
        # present and is otherwise identical to utf-8.
        owners = json.load(open(owners_path, encoding="utf-8-sig"))
        known = {o[0] for o in OUTCOMES}
        unknown = set(owners) - known
        if unknown:
            raise SystemExit("owners file names unknown outcomes: %s" % sorted(unknown))

    confirmed = bool(owners_path)
    requirements = read_requirements()

    # An owners file that names nobody does not confirm anything. Treat it as the
    # illustrative build rather than flipping CONFIRMED and producing the nonsense
    # marker "Partly confirmed - 0 of 6 owners named". Caught by
    # test_dry_run_reports_a_no_op_as_a_no_op.
    if confirmed:
        named = sum(1 for oid, *_ in OUTCOMES
                    if owners.get(oid, {}).get("owner")
                    and owners.get(oid, {}).get("owner") != "[owner withheld]")
        if named == 0:
            print("  NOTE: owners file names no owner; building the illustrative"
                  " module rather than claiming partial confirmation", file=sys.stderr)
            confirmed = False

    # Everything below this line is generated. Hand edits are lost on rebuild.
    L = []
    L.append('"""The October 16 deliverable: the Dean\'s dashboard, Option A.')
    L.append("")
    L.append("GENERATED by scripts/build_oct16_data.py. Do not hand-edit: a rebuild")
    L.append("overwrites this file. Change the generator, or pass --owners.")
    L.append("")
    if confirmed:
        L.append("CONFIRMED: built WITH an owners file, so the figures are confirmed by")
        L.append("the people accountable for them and the page says so.")
    else:
        L.append("CONFIRMED: built WITHOUT an owners file. Every figure is illustrative")
        L.append("and no owner is named, which the page states.")
    L.append("")
    L.append("Option A was chosen 2026-10-07. Static by design: the brief for this view")
    L.append('says "Static, clickable pages; no live data feeds".')
    L.append('"""')
    L.append("")
    L.append("# Whether these figures are confirmed by their owners. Derived from how")
    L.append("# this module was built, never set by hand and never an app setting, so a")
    L.append("# redeploy or a data swap cannot leave the marker wrong.")
    L.append("CONFIRMED = %r" % confirmed)
    L.append("")
    L.append('DATA_STATUS_ILLUSTRATIVE = "Illustrative \\u2014 format only, not CLL results"')
    L.append('DATA_STATUS_CONFIRMED = "Confirmed by each owner"')
    L.append("")
    L.append("")
    L.append("def data_status() -> str:")
    L.append('    """The marker text, chosen from how this module was built.')
    L.append("")
    L.append("    Reports a PARTIAL state rather than rounding to confirmed. A page where")
    L.append("    some owners are named and others are not must not claim the whole is")
    L.append("    confirmed - the confirmed-data spec requires the service to distinguish")
    L.append("    them rather than mark the dataset one way.")
    L.append('    """')
    L.append("    if not CONFIRMED:")
    L.append("        return DATA_STATUS_ILLUSTRATIVE")
    L.append("    named = sum(1 for o in OUTCOMES if owner_is_confirmed(o[\"owner\"]))")
    L.append("    if named == len(OUTCOMES):")
    L.append("        return DATA_STATUS_CONFIRMED")
    L.append('    return "Partly confirmed \\u2014 %d of %d owners named" % (named, len(OUTCOMES))')
    L.append("")
    L.append("")
    L.append("# Three owner states. A withheld name is a marked placeholder and is never")
    L.append("# treated as a confirmed owner.")
    L.append('OWNER_WITHHELD = "[owner withheld]"')
    L.append('OWNER_NONE = "no owner named"')
    L.append("")
    L.append("")
    L.append("def owner_label(owner) -> str:")
    L.append('    """How to show an owner position."""')
    L.append("    return OWNER_NONE if owner is None else owner")
    L.append("")
    L.append("")
    L.append("def owner_is_confirmed(owner) -> bool:")
    L.append('    """A withheld or missing owner is not a confirmed owner."""')
    L.append("    return bool(owner) and owner != OWNER_WITHHELD")
    L.append("")
    L.append("")
    L.append("# How an outcome's progress is shown. The page previously computed this in")
    L.append("# its template, so the bar's meaning lived in the view while this module")
    L.append("# documented it as derived. It lives here now, and the template renders")
    L.append("# the value it is handed (the oct16-deliverable spec, design D5).")
    L.append("def percent(outcome) -> int:")
    L.append('    """Milestones reached as a whole percent of those planned, floored.')
    L.append("")
    L.append("    Floored, not rounded: a bar that reads 50% when fewer than half the")
    L.append("    milestones are reached would overstate progress, and this page exists")
    L.append("    to not do that.")
    L.append('    """')
    L.append("    planned = outcome[\"planned\"] or 0")
    L.append("    if planned <= 0:")
    L.append("        return 0")
    L.append("    return (100 * outcome[\"reached\"]) // planned")
    L.append("")
    L.append("")
    L.append("# Page furniture, from the wireframes.")
    L.append('EYEBROW = "OCTOBER 16 \\u00b7 THE DEAN\'S DASHBOARD"')
    L.append('TITLE = "The Dean\'s six Blueprint outcomes"')
    L.append('SUBTITLE = "Each outcome shown by milestones reached, until its KPIs have data"')
    L.append("EXPLAINER = (")
    L.append('    "Built on P01\\u2013P06 from the Blueprint for 2027. Progress = milestones "')
    L.append('    "reached of milestones planned, reported by each owner."')
    L.append(")")
    L.append("AS_OF = %r  # set at the data cutoff when confirmed" % (None,))
    L.append("")
    L.append("SOURCE_NOTE = (")
    L.append('    "Outcomes, headings and the scope figures: the October 16 wireframes, "')
    L.append('    "Option A. The data-requirements table: Oct16_Wireframe_Data_Lists.xlsx, "')
    L.append('    "\'Option A Data\'. Outcome names and target wording also appear in the CLL "')
    L.append('    "KPI Atomic Definitions Master, Metrics sheet, which the wireframes cite "')
    L.append('    "as their source for target text."')
    L.append(")")
    L.append("")
    L.append("# What this view collects by October 16.")
    L.append("SCOPE = [")
    for a, b, c in SCOPE:
        L.append("    (%r, %r, %r)," % (a, b, c))
    L.append("]")
    L.append("")
    L.append("# Both sides, so a reader can decide from the page.")
    L.append("TRADE_OFFS = [")
    for good, text in TRADE_OFFS:
        L.append("    (%r, %r)," % (good, text))
    L.append("]")
    L.append("")
    L.append("OUTCOMES = [")
    for oid, name, status, reached, planned, summary, mslist in OUTCOMES:
        entry = owners.get(oid, {})
        # The count is DERIVED from the list, not carried separately: the scaffold's
        # `planned` (4) disagreed with the three milestones it listed, so the card
        # said "1 of 4" above only three rows. Counting the list makes the number
        # and the rows impossible to drift. `reached` counts the Met milestones.
        reached = sum(1 for _, st in mslist if st == "Met")
        planned = len(mslist)
        L.append("    {")
        L.append('        "id": %r,' % oid)
        L.append('        "name": %r,' % name)
        L.append('        "status": %r,' % status)
        L.append('        "reached": %d,' % reached)
        L.append('        "planned": %d,' % planned)
        L.append('        "summary": %r,' % summary)
        L.append('        "owner": %r,' % entry.get("owner"))
        L.append('        "updated": %r,' % entry.get("updated"))
        L.append('        "milestones": [')
        for mn, ms in mslist:
            L.append("            (%r, %r)," % (mn, ms))
        L.append("        ],")
        L.append("    },")
    L.append("]")
    L.append("")
    L.append("# The full 'what it takes to show this on October 16' table: one row per")
    L.append("# data element, with where it comes from and whether we have it. Read from")
    L.append("# the wireframe's own workbook rather than retyped, so the page and the")
    L.append("# workbook cannot drift apart.")
    L.append("DATA_REQUIREMENTS = [")
    for r in requirements:
        L.append("    {")
        for key in ("id", "section", "element", "definition", "example", "volume",
                    "source", "provided_by", "available", "how", "needed"):
            L.append("        %r: %r," % (key, r[key]))
        L.append("    },")
    L.append("]")
    L.append("")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owners", help="JSON file of confirmed owners")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    path = build(args.owners, args.out)

    import importlib.util
    spec = importlib.util.spec_from_file_location("oct16_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    print("Built %s" % path)
    print("  CONFIRMED   : %s" % mod.CONFIRMED)
    print("  marker reads: %s" % mod.data_status())
    named = sum(1 for o in mod.OUTCOMES if mod.owner_is_confirmed(o["owner"]))
    print("  outcomes    : %d, of which %d have a confirmed owner"
          % (len(mod.OUTCOMES), named))


if __name__ == "__main__":
    main()
