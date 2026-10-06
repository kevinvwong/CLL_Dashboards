"""Extract the five canonical goals from the Strategy 2035 deck into a source file.

Task 2.1. The deck is the authority both other sources name; its slide 7 carries
the five goals verbatim. This reads them from the deck rather than retyping them,
and records the slide as provenance, so the seed cannot drift from the source.
"""
import html
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET

D = r"C:\Users\kwong318\Downloads"
DECK = os.path.join(D, "CLL-strategy-2035-presentation.pptx")
OUT = (r"C:\Users\kwong318\GitHub\CLL_Dashboards\ospec\db\canonical_goals.py")

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

z = zipfile.ZipFile(DECK)


def slide_text(n):
    root = ET.fromstring(z.read("ppt/slides/slide%d.xml" % n))
    out = []
    for para in root.iter(A + "p"):
        line = "".join(t.text or "" for t in para.iter(A + "t")).strip()
        if line:
            out.append(line)
    return out


lines = slide_text(7)
print("=== slide 7, verbatim ===")
for l in lines:
    print("  ", l)

# "Goal N: <text>"
goals = {}
for l in lines:
    m = re.match(r"Goal\s+(\d)\s*:\s*(.+)$", l)
    if m:
        goals[int(m.group(1))] = m.group(2).strip()

vision = None
for l in lines:
    m = re.match(r"College Vision\s*:\s*(.+)$", l)
    if m:
        vision = m.group(1).strip()

print()
print("  goals found:", sorted(goals))
if sorted(goals) != [1, 2, 3, 4, 5]:
    raise SystemExit("did not find five goals on slide 7; refusing to write")

# Short labels. The deck gives no short names; these are the dashboard aliases the
# wireframes and the prototype use, kept consistent with the prototype's six.
SHORT = {
    1: "Academic",
    2: "Extension",
    3: "Learner",
    4: "Research",
    5: "Operational",
}

PY = []
PY.append('"""The five canonical Strategy 2035 goals.')
PY.append("")
PY.append("GENERATED from the canonical deck, not typed. Source:")
PY.append("  CLL-strategy-2035-presentation.pptx, slide 7, \"College Goals: How We Will")
PY.append("  Advance Our Vision\"")
PY.append("")
PY.append("That deck is the authority both the enterprise package and the wireframes")
PY.append("name. The package matches this wording word for word; the prototype's seed")
PY.append("did not - goals 3 and 4 were transposed and goals 2-5 had no title. Fixing it")
PY.append("meant re-seeding from here, not editing rows: a goal's number is its identity,")
PY.append("and editing a number moves the initiatives tagged to it.")
PY.append("")
PY.append("Regenerate with scripts/extract_canonical_goals.py if the deck changes.")
PY.append('"""')
PY.append("")
PY.append("SOURCE = \"CLL-strategy-2035-presentation.pptx, slide 7\"")
PY.append("")
PY.append("VISION = %r" % vision)
PY.append("")
PY.append("# number, short label, canonical title")
PY.append("GOALS = [")
for n in sorted(goals):
    PY.append("    (%d, %r, %r),"
              % (n, SHORT[n], goals[n]))
PY.append("]")
PY.append("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(PY))
print()
print("wrote %s" % OUT)

import importlib.util
spec = importlib.util.spec_from_file_location("cg", OUT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("  VISION set :", bool(m.VISION))
for n, s, t in m.GOALS:
    print("   %d  %-16s %s" % (n, s, t[:74]))
print("  non-ASCII present:", any(ord(c) > 127 for _, _, t in m.GOALS for c in t))
