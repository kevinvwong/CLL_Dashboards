# CLL Strategy Portfolio — Authoritative Source

**Status:** definitive for what it states as settled; every unresolved item is marked
**OPEN** and names who must decide it. Nothing here is a guess dressed as a fact.

**Compiled:** 2026-10-06
**Compiled from:** four independent bodies of work, each read in full. Provenance in §1.

---

## 1. Provenance — what this is built from

| # | Source | Where | What it is |
|---|---|---|---|
| A | `CLL-strategy-2035-presentation.pptx` | `Downloads/` | The canonical strategy deck. 13 slides. Author W. E. Roberts; last modified 2026-01-12. **This is the only document that both other sources call authoritative.** |
| B | `CLL_Strategy_Portfolio_Enterprise_Package_v1.0.zip` | repo root (gitignored) | Rev2 governance baseline: 27 tables, 25 objectives, 11 targets, ADR set, constraint tests. |
| C | `CLL KPI Dashboard Wireframes and Mockups.pdf` (+ ` (1)`) | `Downloads/` | The Oct 16 UI programme. 13 and 20 pages; the two versions differ (§6). |
| D | PMO Master Package v6 (`00_`…`07_`, incl. `07_CLL_KPI_Atomic_Definitions_Master.xlsx`) | `Downloads/` | The Board suite: 35-KPI dictionary, registry, ClickUp bridge, timeline, named people. |
| E | running prototype | `ospec/` + live App Service | The nine-table prototype and its 203 tests. |

**Source hierarchy used here**, taken from the package's own rule (README §3) and
corroborated by the deck's ownership:

1. **Canonical strategy** — the Strategy 2035 deck governs goals, objectives and targets.
2. **Operating model** — workshop transcript and whiteboard govern priorities, ownership, updates.
3. **Corroborating** — supporting dashboards and workbooks inform but **do not override** canonical strategy.

---

## 2. SETTLED — the five goals

Verified directly against `CLL-strategy-2035-presentation.pptx` slide 7, not against
a summary of it. **Canonical wording, verbatim:**

| # | Goal |
|---|---|
| 1 | Catalyze a learning society and build the world's home for transformative learning systems leaders. |
| 2 | Empower communities with limitless learning and scale our extension model for global impact. |
| 3 | Engage 5 million learners with Georgia Tech–designed lifetime learning touchpoints. |
| 4 | Be the global thought leader in optimized learning systems. |
| 5 | Revolutionize an operational model that is seamless, data-rich, proactive, and delivers a learner-first experience. |

Also canonical, slide 7: **College Vision** — *"To be the catalyst for limitless
learning that transforms lives through access, innovation, and relevance."*

### This settles blocker #3 and two apparent conflicts

Three goal lists were circulating. Two of them were never in conflict:

- The **package (B) matches the deck (A) word for word.** It is a faithful transcription.
- The **prototype (E) is wrong.** Goals 3 and 4 are transposed, goal 1 carries a
  truncated paraphrase, and goals 2–5 have no title at all. **Fix the prototype.**
- The **wireframes' five "goals" are not goals.** Each traces to an objective on
  slides 8–12 (§3), not to slide 7. They are a *metrics view of the goals*, labelled
  "GOAL n" for layout. Not an alternative goal list.

---

## 3. SETTLED — 25 objectives, and where the wireframes' five lines come from

Slide 7 defines 5 goals; slides 8–12 carry **25 objectives** beneath them
(4, 4, 7, 6, 4). The package stores all 25 as `strategic_objective`.

The wireframes' five headline lines map onto objectives, verified:

| Wireframes line | Actually drawn from |
|---|---|
| "Field-defining degrees at every level" | Goal 1 objective 2 — *Launch field-defining degrees at every higher education level by 2029…* |
| "Global network of 200 hubs" | Goal 2 objective 2 — *Create a global network of connected learning with at least 200 hubs by 2035…* |
| "Empower 5 million learners" | Goal 3 **title** (slide 7) |
| "$20M annual research" | Goal 4 objective 6 — *Grow the research portfolio to $20M in annual expenditures…* |
| "Educate 10% of Fortune 500 L&D leaders" | Goal 1 objective 4 — *Shape the field so that at least 50 learning leaders from Fortune 500 organizations hold one of our credentials…* |

**Do not use the wireframes' five lines as a goal list.** Objective text is not goal
text, and the package forbids overwriting canonical goal wording.

---

## 4. SETTLED — the metric taxonomy, and it reconciles

The PMO's "35 KPIs" is not a rival taxonomy. It is exactly the wireframes' model:

```
35 cascading KPIs
  =  6 Dean outcomes          P01–P06        (the "Blueprint for 2027")
  + 29 team KPIs              13 EXP + 2 ECO + 8 INF + 6 FUT
  = 35
```

Verified by reading `07_CLL_KPI_Atomic_Definitions_Master.xlsx` sheet `Metrics`:
41 rows = 1 header + 40 records, of which **6 are `Dean outcome`**, **29 are team
KPIs** across four teams, and **5 are `Strategy 2035 goal`** rows.

| Level | Count | IDs |
|---|---|---|
| Strategy 2035 goals | 5 | `2035-G1`…`2035-G5` |
| Dean outcomes | 6 | `P01`…`P06` |
| Team 01 · Learning Experiences | 13 | `EXP-01`…`EXP-13` |
| Team 02 · Learning Ecosystems | 2 | `ECO-01`, `ECO-02` |
| Team 03 · Learning Infrastructure | 8 | `INF-01`…`INF-08` |
| Team 04 · Learning Futures | 6 | `FUT-01`…`FUT-06` |

Of the 40 records, `Class` is: **6 Dean outcome**, **8 Source target**, **21 Needs
review**, **5 Strategy 2035 goal**. `Target status` is `Proposed – approval pending`
for 27, `Approved – source` for 8, `Strategic reference – validate` for 5. **Pipeline
status is `Not started` for all 40.**

### The PMO package claims more resolution than its own workbook shows

`01_cll_pmo_gap_closure_master_v6.pdf` states it *"resolves the 21 previously
unfinalized metrics ('needs review' in prototype files)"*. The workbook does not
agree: its own `Class` column still marks **exactly 21 rows `Needs review`**, only 8
are `Approved – source`, and every one of the 40 is `Not started`.

So the definitions are **written** but **not approved** — which is consistent with
the talking-points document requesting *"Board endorsement"* rather than reporting an
approval. **Treat the 35 KPIs as drafted, not governed.** Do not report them as
settled.


### The full stack, with every layer named

```
Strategy 2035 goals (5)                     canonical, deck slide 7
        |
   25 objectives                            canonical, deck slides 8-12
        |
   6 Dean outcomes  P01-P06                   Blueprint for 2027
        |
   4 teams                                   01 Experiences / 02 Ecosystems /
        |                                    03 Infrastructure / 04 Futures
   29 team KPIs                               EXP / ECO / INF / FUT
        |
   components                                e.g. EXP-01a, EXP-01b
        |
   milestones                                the unit of Oct 16 progress
```

**Three layers of this stack are in no schema we hold**: Dean outcomes, teams, and
components. Rev2 (B) has Goal → Objective → Target → Initiative → Metric Version.
The prototype (E) has Goal → Initiative. Neither can express the middle of the real
model. The PMO workbook (D) is the only artifact that describes it.

---

## 5. SETTLED — the governed metric definition model

The KPI workbook defines each metric with fields that no schema we hold carries.
This is the strongest single contribution of the PMO package and should be adopted
wholesale:

| Field | Why it matters |
|---|---|
| **Population (denominator)** | A count without its denominator is not a metric. |
| **Qualifying condition (numerator)** | The rule that makes a row count. |
| **Grain** | What one row of the source is (e.g. "one row per asset review"). |
| **Unit of count** | What is being counted. |
| **Included / Excluded** | Explicit scope, in words. |
| **Derived fields** | e.g. `latest_review = review with max review_date per asset`. |
| **Data quality rules** | e.g. "reviewer is never the asset owner". |
| **Gaming controls** | e.g. "reviewing only assets known to pass → all new external assets reviewed plus a random quarterly sample". |
| **Time and history** | Snapshot vs cumulative, and effective dating. |
| **Companion measure** | The counter-metric that stops the primary measure being gamed. |
| **Definition version / open decisions / pipeline status** | Change control on the definition itself. |

The **gaming controls** and **companion measures** are the part to keep above all
else. They are what the package's ADR set calls governance and what a dashboard
without them lacks.

---

## 6. SETTLED — the priority list, corrected 2026-10-06

**This section previously read "OPEN — the priority list is genuinely unresolved".
That was wrong, and the error is corrected here rather than deleted.**

I had recorded two competing sets of six. Reading the Dean's prototype at
`cll-blueprint-2027.wag32002.chatgpt.site` shows the package and the prototype
**agree**: the package's six **short names** and the prototype's six **long names
are the same six**. Verified one by one, 6 of 6:

| Package | Prototype / PMO workbook / wireframes Option A |
|---|---|
| `Identity` | P01 One Shared Identity |
| `Innovation` | P02 Champion Innovation |
| `Pathways` | P03 Integrated Portfolio & Pathways |
| `Scale` | P04 Quality at Scale |
| `Data` | P05 Data-Informed Action |
| `Culture` | P06 Culture & Learning |

Three independent artifacts carry these six **word for word**: the **Dean's
prototype**, the **PMO KPI workbook**, and the **wireframes' Option A**.

### The remaining conflict, stated correctly

The second set is the **May 13 deck's**, which the wireframes' *Option B* draws on:

`Culture · Financial Model · Operating Model · Field of Study · Content and Product · Technology and AI`

Checked against both the package and the prototype: **five of those six appear in
neither** — only `Culture` is common, and that is a shared word, not a shared
priority.

So the question is **not** "which of two sets of six". It is: **the operational
system — package, prototype and PMO workbook, all agreeing — versus the May 13
deck that Option B uses.** The canonical Strategy 2035 deck contains no priorities
at all, so it does not arbitrate.

### Consequence for October 16

**The page we shipped uses the agreed six.** Option A's cards are P01–P06, which
are the package's and the prototype's six. That is a second, independent reason
Option A was the safer choice.

---

## 7. OPEN — which wireframe version is current

Two versions exist; they disagree materially:

| | 13-page | 20-page |
|---|---|---|
| October 16 options | **three** (A outcomes, B priorities, C Infinity) | **two** (A outcomes, B Infinity) |
| Six-priorities view | offered as an Oct 16 option | moved out, "now in Stage 2" |
| Roadmap page | absent | present |
| File timestamp | earlier | later |

The 20-page reads as the later narrowing, but **nothing states precedence** and both
were downloaded in one session. One residue of the edit: its page 8 still says
"Wireframe 2 of **3**" while pages 9–10 say "of 2". **Confirm which is current.**

---

## 8. SETTLED — the delivery plan and what it is honestly not

From the wireframes and the Oct 16 data workbook:

```
Oct 5   retreat
Oct 7   Dean picks an option
Oct 8-9 milestone lists and owners confirmed
Oct 13  data cutoff
Oct 14-15 build and review
Oct 16  first deliverable
```

Stage 1 reports **milestones reached of milestones planned**, *"instead of KPI values
we cannot yet calculate"*. Explicitly **not**: KPI values, the six-priorities view, or
the PMO tool.

Data readiness, as the programme states it: **8 of 16** required elements in hand for
Option A, **5 of 10** for Option B. Blocking gap in both: **no owners are named yet.**

Data inventory: 390 fields across 6 phases; 0% checked in Phase 4 (institutional) and
Phase 5 (Strategy 2035 cross-platform). Access requests 2 of 5 granted.

---

## 9. SETTLED — what to do with the prototype (E)

The prototype is **not** the Oct 16 deliverable and never was. It is also not Rev2.
It is a working nine-table demonstration built on a priority set that may be the
wrong one and a goal list that is provably the wrong one.

Three things are true and not in conflict:

1. **Its goal list is wrong** and must be re-seeded from slide 7, not corrected in place.
2. **Its priority list may be wrong** and cannot be fixed until §6 is decided.
3. **It is nonetheless the only working implementation of the Goal/Priority/Initiative/Person card model**, and the deck, the package and the wireframes all agree that model is wanted.

**Recommendation:** keep it deployed on sample data, relabel it as synthetic (already
done), and treat it as evidence for the Stage 2 build rather than as a baseline to
extend. Do not invest further in its nine-table schema.

---

## 10. What this document does not establish

- **The priority list** (§6) — needs a decision, not more reading.
- **Which wireframe version is current** (§7).
- **Whether Stage 1 and the prototype are the same track.** They share a name and a
  vocabulary and nothing else. This is unresolved and it governs what work is
  worth doing next.
- **Any business data.** The package ships canonical strategy and **zero** operational
  rows; everything operational in this repo is invented or illustrative.

---

## 11. Decisions required

| # | Decision | Owner | Blocks |
|---|---|---|---|
| 1 | Which six priorities are real, B's or C's | Dean / strategy owner | The prototype's seed, the home screen, Rev2's `annual_priority` |
| 2 | Which wireframe version is current | PMO lead | The Oct 16 build |
| 3 | Is Stage 1 the prototype, or a parallel track | PMO lead | Whether prototype work continues |
| 4 | Adopt the Dean-outcome / team / component layers | Dean / PMO | Rev2 schema, if Rev2 is to be the Stage 2 backend |
| 5 | Is Rev2 the Stage 2/3 backend, or superseded | PMO / governance | Whether the Rev2 work stands |
