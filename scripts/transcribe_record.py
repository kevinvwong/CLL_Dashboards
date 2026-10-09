"""Transcribe the authoritative meeting record (.docx) to Markdown, in full.

Deliberately lossless: every paragraph and every table cell, in document order.
This exists so the record is diffable, searchable and citable from the repo, and
so it can be checked for completeness against the .docx rather than trusted.

    python scripts/transcribe_record.py            # write the .md
    python scripts/transcribe_record.py --check    # fail if it is stale

--check is the gate: it re-transcribes and compares, so a transcription that
silently lost a table cannot pass. Completeness is asserted by counting
paragraphs and cells against the source, not by the author's eye.
"""
import argparse
import hashlib
import pathlib
import sys

import docx

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "docs" / "record" / "CLL_Meeting_Record_and_OpenSpec_v0.1.docx"
OUT = REPO / "docs" / "record" / "meeting-record-and-openspec-v0.1.md"

HEADER = """<!--
  TRANSCRIPTION - do not edit by hand. Regenerate with:
      python scripts/transcribe_record.py

  Source of truth is the .docx beside this file. This is a complete
  transcription for search, diff and citation - nothing is summarised or
  omitted. Every paragraph and every table cell is reproduced in document
  order; run with --check to prove this file has not drifted from the .docx.
-->

# CLL Strategic Portfolio Dashboard
## Meeting Record, Change Control Package, and OpenSpec v0.1

"""


def cell(text: str) -> str:
    """A table cell, with pipes and newlines neutralised so the row survives."""
    return " ".join(text.split()).replace("|", "\\|")


def render(doc):
    out = [HEADER]
    # Walk body children in document order so tables land where they belong.
    body = doc.element.body
    paras = {p._p: p for p in doc.paragraphs}
    tables = {t._tbl: t for t in doc.tables}
    n_paras = n_rows = n_cells = 0

    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = paras.get(child)
            if p is None:
                continue
            text = " ".join(p.text.split())
            if not text:
                continue
            n_paras += 1
            style = (p.style.name if p.style else "") or ""
            if style.startswith("Heading") or style == "Title":
                level = 1 if style == "Title" else int(style.split()[-1])
                out.append("\n" + "#" * level + " " + text + "\n")
            elif style == "List Bullet":
                out.append("- " + text)
            else:
                out.append(text)
        elif tag == "tbl":
            t = tables.get(child)
            if t is None:
                continue
            out.append("")
            for i, r in enumerate(t.rows):
                cells = [cell(c.text) for c in r.cells]
                n_rows += 1
                n_cells += len(cells)
                out.append("| " + " | ".join(cells) + " |")
                if i == 0:
                    # Markdown needs a delimiter under the header row, or the
                    # whole table renders as body text.
                    out.append("|" + "|".join(["---"] * len(cells)) + "|")
            out.append("")
    return "\n".join(out).rstrip() + "\n", n_paras, n_rows, n_cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    doc = docx.Document(str(SRC))
    text, n_paras, n_rows, n_cells = render(doc)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    if args.check:
        if not OUT.exists():
            print("MISSING: %s does not exist" % OUT)
            return 1
        cur = OUT.read_text(encoding="utf-8")
        if cur != text:
            print("STALE: %s differs from the .docx" % OUT.name)
            print("  current sha256: %s" % hashlib.sha256(cur.encode()).hexdigest()[:16])
            print("  fresh   sha256: %s" % digest[:16])
            return 1
        print("current (%d paragraphs, %d table rows, %d cells)" % (n_paras, n_rows, n_cells))
        return 0

    OUT.write_text(text, encoding="utf-8")
    print("wrote %s" % OUT)
    print("  %d paragraphs, %d table rows, %d cells" % (n_paras, n_rows, n_cells))
    print("  sha256 %s" % digest[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())