# Board Release Plan — derived from the authoritative meeting record

**Status:** approved for execution, 2026-10-09
**Authority:** `docs/record/` — the meeting record with the Dean and COO (v0.1).
That document outranks this repository wherever the two disagree.

This file is the executable reading of the record: every requirement, change
request and acceptance criterion mapped to a phase, with its state verified
against the code rather than assumed. It lives outside `docs/guide.yaml`, so it
is not served in the app.

## The binding constraint

```
TeamInitiativeUpdates   0 rows
Team Initiatives        29 — all "Not started"
Dean Initiatives        FY26: 3 @ 100%   FY27: 8 @ 22.5% mean
Milestones              18 (6 Met / 6 In progress / 6 Not started)
```

**AI-001 — "Coordinate percent-complete input for all initiatives" (Elizabeth /
team leaders, Critical, Immediate) — is the binding constraint on the whole
demonstration, and it is a people dependency, not an engineering one.** Until
owner estimates exist, AC-003, AC-004 and AC-008 cannot be met, and the
telemetry row has nothing truthful to say about 29 of 29 initiatives.

Phases A–D make the product correct and honest. They do not make the demo good.
That gap is raised with the Data Owner before rehearsal, not at it.

## Already satisfied (verified, not assumed)

| Item | Evidence |
|---|---|
| FR-001 four-view model | `/goals`, `/outcomes`, `/teams`, `/dean-initiatives` all read one model |
| FR-010 Dean→team crosswalk | `TeamInitiativeDeanLinks`, crosswalk shown on the Dean page |
| FR-006 / CR-002 milestone layer | `Milestones` table, 18 rows, four statuses |
| FR-014 no false zero | `No update yet`; `is not none` guards on every progress bar |
| CR-001 percent-complete capture | `TeamInitiativeUpdates` model + write path (no data yet) |
| CR-012 crosswalk validated | Leadership praised it in the transcript |

## Phase A — Record into the repository — **delivered** (4a8d164)

Store the authoritative record in full, and keep it out of the app.

- `docs/record/` holds the original `.docx` **and** a complete Markdown
  transcription — all 14 tables, every row, no summarising.
- **No `guide.yaml` entry.** `app/docs.py` renders only manifest-listed files
  and never reads `.docx`, so the record is unreachable from the running app.
- A `README.md` states that this record outranks the repository, and preserves
  the document-control block's own status line — *"Draft authoritative project
  record for validation"* — verbatim rather than quietly upgrading it.
- Repoint the glossary, ADR-0006 and the deploy runbook at it where they
  currently assert things the record supersedes.

## Phase B — Board UX (CO-001, Change Order 1) — **delivered** (837571e)

**CR-005 / FR-003 — full Strategy 2035 goal language.** The register, card and
goal pages render `Goals.ShortName` ("Academic", "Learner"). D-003 and the
transcript require the full language, which is already loaded in
`Goals.FullName`. Render `FullName`; keep `ShortName` as the compact fallback
only where space is genuinely constrained. This also finishes the abbreviated
label introduced on 2026-10-09.

**CR-011 / FR-009 / D-009 — hide Source Area from standard views, retain it in
the store.** Remove the column header and cell from `_mi_table.html`, `team.html`
and `team_initiative.html`. Keep `SourceAreaID` in the database for lineage.
Withdraw the Source Area entry from the user glossary, since it stops being a
term a reader meets.

**CR-003 / FR-007 / AC-007 — list and card presentations.** The register
renders one table row per initiative today. 29 rows is the dense case; a
team-filtered subset is the sparse one.

**Persistence decision — URL authoritative, `localStorage` fallback.**

```
?view=card present  → that view wins (shareable, survives reload, hand-off)
else localStorage   → that view is the default
else                → density-aware default
```

Rationale: the record makes the URL the demonstrable artefact (AC-009 rehearsed
route, CR-018 Critical), so a presenter who switches view must be able to hand
someone a link *in that view* — a localStorage-only preference cannot travel.
`localStorage` holds the *default* because a presentation preference is not
state: no schema, no server round-trip, no per-user row.

The density-aware default is evaluated **once**, and never re-evaluated as
filters change mid-session — a view that flips under a reader is worse than one
that is merely suboptimal. An explicit user choice always wins.

Accessibility: a real control pair with `aria-pressed`, not a styled `div`;
the choice is announced; the reduced-motion path applies when card view animates.

**AC-002 — regression evidence** that the Consult GT routing defect and the
"unexpected side panel" defect stay closed.

## Phase C — Interim measurement (CO-002) — **delivered** (5a11480)

**AC-004 / NFR-005 — percent-complete must be clearly identified.** Per the
record's own Progress Update entity, which carries *percent complete, narrative,
update date, and source*:

- where an update exists — the owning person and the update date beside the bar
- where none exists — a plain **"Owner estimate — not yet supplied"**, never a
  bare percentage and never a zero

A static label alone cannot satisfy "clearly identified"; the doc requires the
source to be identifiable.

## Phase D — Telemetry (CO-004) and CR-016 — **delivered**

Replaces the static homepage counts. Three indicators, all backed by loaded data:

1. **Dean layer** — FY26 complete (3 of 3), FY27 in flight (8, mean 22.5%)
2. **Milestones** — 6 of 18 met
3. **Awaiting owner estimates** — 0 of 29 supplied

The third is deliberate. It implements AC-005 and AC-008 honestly: the row states
the real gap instead of rendering "29 Not started", which reads as a scorecard of
failure when it only means the diary is empty.

This completes the 2026-10-09 landing-page pass, which removed duplicated counts
but added nothing.

> **Amended 2026-10-09 after implementation: it is FOUR indicators, not three.**
> Removing the static band deleted the "need review" affordance with it — its
> proportion bar and its deep link into the filtered register — and three tests
> failed saying so. That route into the work queue is load-bearing, so it is
> restored as a fourth indicator. The plan's own reasoning for keeping the row
> short ("a row that needs reading is a row that is not read") still holds at
> four; it did not hold at three, because three meant losing a capability rather
> than gaining tidiness.

## Phase H — Hosting (CO-009), separate track

NFR-001 and AC-001 require an approved institutional demonstration host.
Today neither qualifies: Azure sits on a student subscription the record
explicitly flags as non-institutional (D-013, R-005, AI-013), and the VPS has
no organisational authentication at all. Blocked on explicit Azure approval.

## Scheduled, not in the first pass

| Phase | Order | Work |
|---|---|---|
| **F** | CO-005 | Workbook upload → validation → versioned refresh (FR-012/CR-007). Only a *generated static* module exists today; no bridge. A build in its own right. |
| **E** | CO-003 | Milestone definitions, placeholders, priority rollups |
| **G** | CO-006 | Role on person (FR-011), editing (FR-013), Dean escalation powers (Q-003) |
| **I** | CO-007/008 | Capacity analytics and M365 ingestion — **discovery only**, post-board |

## Phase J — OpenSpec reconciliation

After A. The four Rev2 changes are complete but unarchived, and
`openspec/specs/` is empty — archiving publishes their requirements as settled
fact, including one that requires `set_person_pin` / `verify_person_pin`, removed
on 2026-10-09. Reconcile each against this record, correct the stale
requirement, then archive.

## Open questions carried from the record

- **Q-001** telemetry indicators — *resolved in Phase D*, subject to review.
- **Q-002** how rollups are calculated when measures differ — after board release.
- **Q-003** Dean's final permissions and escalation powers — separate governance.
- **Q-004** which meeting event is the authoritative record — confirm before the
  package is attached or published to a meeting record.