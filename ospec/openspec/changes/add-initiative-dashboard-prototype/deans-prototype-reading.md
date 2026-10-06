# The Dean's prototype: `cll-blueprint-2027.wag32002.chatgpt.site`

Read 2026-10-06. This is the **"Dean's Blueprint (prototype site)"** the wireframes
name as a data source. It is a live working prototype and it is the most detailed
artifact yet: a governed KPI cascade with the full 35-KPI model.

## What it is

| | |
|---|---|
| Title | *Blueprint for 2027 \| CLL KPI Cascade* |
| Version | Blueprint v0.1 · "Working draft for FY2027 planning" |
| Header counts | **6 priorities · 35 cascading KPIs · 21 need review** |
| Views | Blueprint (executive map), Team cascade, Coverage |
| Export | `Blueprint_for_2027_KPI_Register.xlsx` (4 sheets) |
| Footer sources | `CLL_FY2027_Goals_by_Area.xlsx` · `KPI Gaudelli(2).xlsx` |
| Assets | `data.js` (all content), `app.js`, `styles.css` |

## The finding that settles a blocker: three sources agree, and the package maps onto them

The six priorities in **the Dean's prototype**, **the PMO KPI workbook**, and **the
wireframes' Option A** are **identical, word for word**:

```
P01 One Shared Identity
P02 Champion Innovation
P03 Integrated Portfolio & Pathways
P04 Quality at Scale
P05 Data-Informed Action
P06 Culture & Learning
```

And the **enterprise package's** six — which I had recorded as a competing set —
are the *same six under short names*. Verified one by one:

| Package | Prototype |
|---|---|
| `Identity` | P01 One Shared Identity |
| `Innovation` | P02 Champion Innovation |
| `Pathways` | P03 Integrated Portfolio & Pathways |
| `Scale` | P04 Quality at Scale |
| `Data` | P05 Data-Informed Action |
| `Culture` | P06 Culture & Learning |

**6 of 6 map.**

### What this means for the open question

I had recorded "two sets of six priorities" as unreconciled. That was half wrong:

- The package's short names and the prototype's long names are **one set, two namings**.
- The genuine second set is the **May 13 deck's** — `Culture, Financial Model,
  Operating Model, Field of Study, Content and Product, Technology and AI` — which
  appears in **neither** the package nor the prototype. Checked: all six are absent
  from both.

So the conflict is not "two sets of six priorities". It is: **the operational
system (package + prototype + PMO workbook, all agreeing) versus the May 13 deck
the wireframes' Option B draws on.** One of those two is authoritative, and that is
a smaller, sharper question than the one I recorded.

### And Option A is built on the agreed set

The wireframes' Option A cards — P01–P06 — are the prototype's six. So **the page I
shipped for October 16 uses exactly the priorities the Dean's own prototype uses.**
Option A was the safer choice for this reason too, not only for its data count.

## The prototype's data model, in full

**Priorities** (`PRIORITIES`) — each with `code`, `title`, `short`, `description`,
`measure`, `target`, `cadence`, `owner`, `color`. This is a governed definition
per priority, richer than the package's `Priorities` table and richer than the
wireframes' cards.

**Goals** (`GOALS`) — **29 entries** across five *source areas*, each with a
Strategy 2035 alignment, the initiatives that serve it, a target, a source slide,
and the priorities it feeds:

| Source area | Goals |
|---|---|
| Content & Product Strategy | 4 |
| Administration & Operations | 6 |
| Strategic Solutions | 4 |
| Research, Development & Innovation | 6 |
| Academic Affairs | 9 |
| **Total** | **29** |

These 29 are the **team KPIs** — matching the PMO workbook's 29 and its four-team
split (13 + 2 + 8 + 6).

**Teams** — Learning Experiences, Learning Ecosystems, Learning Infrastructure,
Learning Futures, each with a description. Plus `SOURCE_AREAS` (five) and a
`TEAM_ASSIGNMENTS` map.

**Initiatives** — 11 with percent complete, sourced `KPI Gaudelli(2).xlsx`:

```
Strategy '35 Develop                100%     GT Infinity 2.0 Public              10%
GT Infinity 1.0 Prototype           100%     OMS AI                             50%
Restruct / Budget Model             100%     Environmental Scan — Lifelong       80%
Department of Learning Systems       20%     Financial & Labor Optimization       0%
Digital Credentials                   5%     Restructure — 4 Learning Teams      10%
                                             Consult GT                           5%
```

## A structural difference worth noting

The prototype inverts the layer I had recorded. In **its** model:

```
Six priorities (Dean outcomes, P01-P06)      <- the top layer
        |
29 team KPIs, grouped by four teams          <- the cascade beneath
        |
11 existing initiatives                      <- baseline signals
```

But the **wireframes' Option A** presents P01–P06 as *outcomes* and the team KPIs
sit under teams. And the **package** has Goal → Objective → Target. Three
different arrangements of overlapping content.

**The prototype's own vocabulary is "priorities".** The wireframes call the same
six "Dean outcomes". The PMO workbook's `Class` column says `Dean outcome` while
its sheet is named `Metrics` and its columns are `Priorities`. So the same six
records are called priorities in one place and outcomes in another. Worth
settling before it reaches the Board, since a reader cannot tell whether
"priority" and "outcome" are the same thing.

## Its own honesty, which is good

Two things it does that I would keep:

- The coverage view is titled *"Where the blueprint is firm—and where it needs
  decisions"*, with the note **"Target completeness, not performance"**. It
  separates *is the target agreed* from *are we hitting it* — the distinction
  everything else blurs.
- The `Planning note` on the register states plainly: *"The six dean achievement
  marks and 21 team achievement marks labeled 'Needs review' were added for the
  blueprint and require leadership confirmation. Eight source targets are carried
  directly from the supplied FY2027 goals workbook."*

That is the same 8 / 21 split the PMO workbook shows, stated honestly. **21 of 35
marks are unconfirmed**, which is what "Blueprint v0.1 Working draft" means.

## A minor defect on their side

The server sends `Content-Type: text/html` **without a charset**. A browser
sniffs and renders correctly, but any non-browser client defaults to
ISO-8859-1 and produces mojibake — `CLL Â· FY2027`, `initiativesâ¦`. Verified:
decoded as UTF-8 the characters are clean (`CLL · FY2027`), so this is a missing
header, not corrupt content. Cheap to fix and worth telling them, because the
register is meant to be exported and consumed.

## What this changes about our work

1. **Priority conflict, restated.** Package + prototype + PMO workbook agree; the
   May 13 deck is the outlier. `AUTHORITATIVE_SOURCE.md` §6 needs correcting: it
   says "two sets of six" when it is really one set named two ways, plus an
   outsider set. **I should fix that.**
2. **`/oct16` is on the agreed priorities.** Confirmed, not assumed.
3. **The prototype is further ahead than the repo.** It has the six priorities
   defined with measures, cadences and owners; 29 team KPIs with Strategy 2035
   alignment; and 11 initiatives with progress. That is the model the Stage 2
   build should follow, and it is better specified than the package's.
4. **Nothing is approved.** 21 of 35 marks need review, all are `Not started`, and
   it labels itself a working draft.

## Not established

- **Whether "priority" and "outcome" are the same thing** in the College's usage.
  The sources use both for the same six.
- **Whether the May 13 deck is real and current.** Nothing I hold contains it.
- **Who owns what.** The prototype's `owner` field is a *team*, e.g. *"Dean +
  Learning Infrastructure"*, not a person. The register's `Named Owner` column is
  empty. So the October 16 owner question is still open.
