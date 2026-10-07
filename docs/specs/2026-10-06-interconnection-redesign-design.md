# Interconnection redesign — design

Date: 2026-10-06
Status: approved by the user, ready for implementation

## Why

A second UI/UX round, asked to "consider the data interconnections, usability,
data presentation and flow." Measuring the data first showed the model is **two
disconnected halves** joined only at the Priority hub:

```
   Goal(5) --+
             +-- Priority(6) --+-- TeamKPI(29) --+-- SourceArea(5)
   Person(5)-+                 |
                               +-- Initiative(22) -- ProgressUpdate(24)
                               +-- Team(4) (isolated: no person, no initiative)
```

Three consequences, each measured not assumed:

- **Goal is unreachable from the home.** The portfolio-dashboard redesign
  dropped the goal section; `links to /goals/: False`. One of the two
  entry-point taxonomies the app exists to show is reachable only by URL.
- **TeamKPIs align to Goals in the canon but we do not store the edge.** All 29
  name their alignment ("Goal 5", "Goals 3 + 4 + 5"); none is linked.
- **Dead-end routes:** no `/teams/{id}`, no `/kpis/{id}`. 4 teams and 29 KPIs
  exist only inside the home dashboard.

## The source that resolves it

The user supplied `CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx`
(2026-10-06), described as the most recent canon. Read in full:

| Sheet | Content |
|---|---|
| Goals | 5 canonical goals (G1..G5) with Strategy 2035 wording |
| Priorities | 6 (P1..P6), all `Needs Review` |
| Initiatives | **29 "major initiatives" MI-001..MI-029**, each with Source Area, **Strategy Alignment**, Status, Validation Category |
| People | **1 row of a claimed 5** — its own Quality Check says `REVIEW` |
| Quality Checks | Goals 5/5 PASS, Priorities 6/6 PASS, Initiatives 29/29 PASS, People 5/1 REVIEW |

**The finding that changed the plan:** the canon's 29 major initiatives ARE our
29 team KPIs — 24 names match exactly, the other 5 are the same work renamed.
There was never a disjoint population. And **every one of the 29 states its
Strategy alignment**, which parses to goal numbers on all 29.

## Decisions taken with the user

| Decision | Chosen |
|---|---|
| Fix the UI only, or the data edges too | **C**: data edges first, then UI |
| Which data edges | **C2**: what the canon supports, and stop where it refuses |

## Goals

- One connected graph: every edge browsable in both directions, no dead ends.
- Goal reachable from the home again.
- A KPI and a Team each have a real page.
- The KPI table scannable, with the `Needs Review` state filterable.

## Non-Goals

- **Person → Team.** The canon's People sheet holds 1 of 5 rows and flags itself
  `REVIEW`. Seeding a team for each person would be invention; the source
  refuses to assert it.
- **KPI → our sample Initiative.** The canon says a major initiative aligns to
  *goals*, not to our placeholder initiatives. An earlier framing of mine
  ("link the KPI to its initiatives") was wrong and is dropped.
- Replacing the 22 sample initiatives with the canon's 29. The canon's 29 are
  the team-KPI layer, which we already hold; the sample initiatives are a
  separate, explicitly-invented demo population.
- The `config.yaml` contradiction is unchanged: this adds tables below D-1.

## Data changes (from the canon, parsed not retyped)

1. **`TeamKPIGoals`** — a new table giving the KPI → Goal edge. Populated by
   parsing each canon initiative's `Strategy Alignment` ("Goals 3 + 4 + 5" →
   goals 3, 4, 5). All 29 parse.
2. **`TeamKPIs.MIId`** — the canon's stable key `MI-001`..`MI-029`.
3. **5 titles renamed** to the canon's exact wording. Safe: no test pins them,
   and every link is by integer `KPIID`.
4. A read model `vw_TeamKPIGoals` (KPI with its goals).

The seed is **generated from the workbook** (`build_team_layer.py` extended),
never hand-typed, and reproduces the canon's own counts.

## UI changes

**New routes**, closing the measured dead ends:

| Route | Shows |
|---|---|
| `/teams/{id}` | a team: description, its KPIs, its source areas |
| `/kpis/{mi_id}` | one KPI: title, MI-id, team, source area, goals, priorities, target, validation, named initiatives |

**Goal page** gains a "Team KPIs aligned to this goal" section — the new edge,
shown from the goal side.

**Home** regains a Goals section beside priorities and teams, closing the
regression.

**Cross-linking:** a KPI's goal chips link to `/goals/n`; a goal lists its KPIs;
a team lists its KPIs; each KPI links to its team.

**Presentation:** the KPI table gains a group-by toggle (team / source area,
reusing the cascade pattern), the MI-id as the row key, and a `needs review`
filter — 21 of 29 need review, the number leadership cares about.

## Scope added during review (2026-10-06)

Two changes the user asked for after seeing the first build, both recorded
here rather than folded in silently:

**Group 5 — the overview was too long.** Measured before the cut: the overview
rendered **55,693 bytes**, of which **67% was the 29-row KPI table**, and every
KPI rendered **twice** (once inside the four team cards, once in the table).
The fix: the table moved to its own page **`/kpis`** (with the filter and
grouping intact), and the overview's sections became compact entry points —
stat band, five goal tiles, six priority cards (code/title/count), four team
cards (name/description/count) — each linking to detail. The governed fields
(measure/target/cadence/owner) now live on the priority page, where the compact
overview card links. Result: **7,999 bytes, an 86% cut, duplication gone.**

**Group 6 — the meeting surface is iced.** Hidden from the primary nav and its
route returns **404**, while the page, its queries (`attention_list`,
`meeting_updates`, `update_deltas`) and its tests remain in the tree. Re-
enabling is **one environment variable** (`MEETING_ENABLED=1`), not a rebuild.
A visitor with a bookmarked URL gets a clean 404, not a stale agenda. The
meeting's own tests now run under the enabled flag so the feature is proven
intact and not merely parked.

## Risks / Trade-offs

- [Renaming 5 titles changes displayed names] → verified nothing pins them and
  links are by id; the change is cosmetically visible only.
- [Adding tables contradicts config.yaml] → recorded already by the previous
  round; this extends the same recorded contradiction rather than adding a new
  silent one.
- [The canon's People sheet is incomplete] → the design stops at goals; People
  stays a placeholder layer and the gap is recorded, not filled.

## Verification

- The rebuild reproduces the canon counts: 5 goals, 6 priorities, 29 KPIs, 29
  MI-ids, and a goal link for each of the 29.
- Every edge traversable both ways; no dead-end route.
- The goal regression closed (home links to `/goals/n`).
- The overview no longer carries the table or a duplicated KPI list; `/kpis`
  carries all 29 and the needs-review filter returns 21.
- The meeting route 404s and its nav item is absent; with `MEETING_ENABLED=1`
  its page and tests still pass.
- Suite green (475 before this change; 507 after).

## Open Questions

None blocking. Deferred: whether Person → Team returns once the canon's People
sheet is completed.

## Terminology corrected (2026-10-06)

The 29 rows this project called "team KPIs" are **not KPIs**. A KPI is a
measured indicator: it carries a unit of count, a grain, a numerator, a
denominator, a target and a cadence (see `07_CLL_KPI_Atomic_Definitions_Master
.xlsx`, `Metrics`; its README: "35 FY27 KPIs + 5 Strategy 2035 goals = 40
measures"). The 29 rows carry none of those. The canon workbook
(`CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx`, 2026-10-06) names
them **Team Initiatives** — its sheet is "Initiatives", its header "Major
Initiatives", its columns are Initiative ID / Initiative Name / Source Area /
Strategy Alignment / Status / Validation Category, and its own Quality Check
reads `Initiatives 29/29 PASS`.

The prototype they came from called them "KPIs", and that word propagated into
the schema, the routes and the UI. Corrected end to end:

| Was | Now |
|---|---|
| `TeamKPIs` / `TeamKPIPriorities` / `TeamKPIGoals` | `TeamInitiatives` / `TeamInitiativePriorities` / `TeamInitiativeGoals` |
| `KPIID` column, `KPICode`/`KPITitle` aliases | `TeamInitiativeID`, `TeamInitiativeCode`/`Title` |
| `vw_TeamKPIs` and the other views | `vw_TeamInitiatives` etc. |
| routes `/kpis`, `/kpis/{id}` | `/team-initiatives`, `/team-initiatives/{MI-id}` |
| UI label "Team KPI" | "Team Initiative" |

The word **KPI** is now reserved for measures that earn it: the six Priorities
carry a real measure/target/cadence, and the outcomes page cites the real KPI
register. The glossary of record is `CONTEXT.md`. The `portfolio-dashboard`
spec was updated too, and one of its requirements corrected: it had claimed the
home lists every KPI in full, which the group-5 cut already made false.
