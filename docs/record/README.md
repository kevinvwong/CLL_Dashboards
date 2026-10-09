# The authoritative meeting record

This directory holds the record of the CLL Strategic Portfolio Dashboard
meeting with the **Dean and the COO**. Where it and the rest of this repository
disagree, **this record wins**.

## What's here

| File | What it is |
|---|---|
| `CLL_Meeting_Record_and_OpenSpec_v0.1.docx` | The original, as received. Untouched. SHA-256 `EF76C0944556F6DC68DC28B14007F66BCD21A09702898A8825EFE3B2D650D550` |
| `meeting-record-and-openspec-v0.1.md` | A complete Markdown transcription — all 14 tables, 128 paragraphs, 618 cells, nothing summarised |
| `../../plan/2026-10-09-board-release-plan.md` | The executable reading of this record: phases, verified state, sequencing |

## Deliberately not in the app

There is **no entry in `docs/guide.yaml`**, so nothing here is reachable from the
running application. `app/docs.py` renders only files the manifest lists, and it
never reads `.docx` at all.

That is a decision, not an omission. The record contains leadership discussion
about participants, capacity concerns and unreleased plans. It belongs in the
repository as an audit artefact and nowhere near a screen a user can reach.

## The document's own status line, preserved

The document-control block describes itself as:

> **Status:** Draft authoritative project record for validation
> **Version:** 0.1

That line is reproduced verbatim in the transcription and is deliberately *not*
upgraded here. The record is authoritative for what the meeting decided; its own
draft status is a fact about the document, and quietly promoting it to "final"
would be exactly the kind of silent edit this repository tries to avoid. Q-004 in
the record — *which event is the authoritative meeting record* — is still open.

## Keeping the transcription honest

The `.md` is generated, never hand-edited:

```
python scripts/transcribe_record.py            # regenerate
python scripts/transcribe_record.py --check    # fail if stale
```

`--check` re-transcribes from the `.docx` and compares byte-for-byte, so a
transcription that silently loses a table cannot pass. It is verified to go red:
truncating the file by 10% produces `STALE` and exit 1.

## What the record changes about this repository

Four decisions in the repository were made without it and are now superseded or
need reconciliation:

- **Source Area** — D-009 hides it from standard views while retaining it in the
  store. It was still rendered in three templates, and the user glossary still
  defined it as a reader-facing term.
- **Goal labels** — FR-003 requires the full Strategy 2035 goal language. The UI
  showed `Goals.ShortName` ("Academic", "Learner"); the full text was already
  loaded in `Goals.FullName`.
- **Homepage counts** — CR-016 replaces them with meaningful timing and status
  indicators, not merely fewer repetitions.
- **Percent complete** — AC-004 requires it to be identified as an owner estimate.
  It currently renders as a bare percentage with no attribution.