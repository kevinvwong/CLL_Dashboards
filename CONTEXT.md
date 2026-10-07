# CONTEXT

The domain vocabulary for the CLL Initiative Dashboard. A glossary, not a spec:
terms here name *what things are*, not how they are built.

## Why this file exists

The prototype this dashboard grew from called its 29 team rows "KPIs". They are
not KPIs: they carry no unit, numerator, denominator, target or cadence. The
mislabel propagated into the schema, the routes and the UI. This glossary fixes
the words so code and conversation use them the same way.

## Terms

**Strategy 2035 Goal** — one of the five long-horizon goals of the College's
Strategy 2035 plan (Learning Systems Leaders, Global Learning Hubs, Learner
Reach, Research Leadership, Digital Transformation). Identified `G1`..`G5`.
*Source:* the canon workbook's `Goals` sheet; the Dean's deck slide 7.

**Priority** (a.k.a. **Annual Priority**) — one of the six FY2027 execution
lenses (Identity, Innovation, Pathways, Scale, Data, Culture). Each carries a
measure, a target, a cadence and an owner. A priority is an *execution lens*,
not itself the thing measured.
*Source:* the `Priorities` sheet (`P01`..`P06`); the PMO register classifies
these same six as "Dean outcomes".

**KPI** — a measured indicator: it has a unit of count, a grain, a numerator, a
denominator (or is explicitly "not a rate"), a target, and a cadence. Nothing
is a KPI without those. The PMO register holds 40 measures: 35 FY27 KPIs (6
Dean outcomes + 29 team-level) and 5 Strategy 2035 goal measures.
*Source:* `07_CLL_KPI_Atomic_Definitions_Master.xlsx`, `Metrics` sheet. Its own
README: "35 FY27 KPIs + 5 Strategy 2035 goals = 40 measures."

> **Do not call a Team Initiative a KPI.** If a row has no measure and no
> target, it is not an indicator.

**Team Initiative** — one of the 29 bodies of work the College will execute,
aligned to one or more Strategy 2035 goals. Identified `MI-001`..`MI-029` (the
stable key) and shown as "Team Initiative 1". A Team Initiative is *work*; a KPI
is a *measurement*. Each has an owner, one or more goals, one or more priorities,
and contributes to one or more Dean Initiatives.
*Source:* the register, sheet "Team KPI Register"; earlier the canon workbook's
`Initiatives` sheet (Quality Check `Initiatives 29/29 PASS`). Columns carry a
name, source area, owner, description, targets — **no measure**, which is why a
Team Initiative is not a KPI.

**Team** — one of the four organizational units accountable for work:
Learning Experiences, Learning Ecosystems, Learning Infrastructure, Learning
Futures. A team is an accountability axis, distinct from a source area.

**Source Area** — the register area a Team Initiative was filed under (e.g.
"Content & Product Strategy"). A source area is where something was *recorded*;
a team is who is *accountable*. The two are different axes and are not
interchangeable.

**Dean Initiative** — one of the 11 workstreams at the top of the model, owned by
the Dean, split **FY26** (3, complete) and **FY27** (8, in flight). Each carries a
primary Priority and a percent-complete. A **Team Initiative rolls up to one or
more Dean Initiatives** — that edge is the "contributes to" relation, and a Dean
Initiative's page lists the Team Initiatives that roll up to it.
*Source:* the register's "Dean KPI 26"/"Dean KPI 27" rows. The register labels
them "KPI"; the app calls them Dean Initiatives, and reserves "KPI" for a measure
(the Dean's rows carry a percent, not a unit/numerator/denominator, so they are
not indicators in this glossary's sense).

## Known tensions

- **The register says "KPI" for both layers; this glossary does not.** The
  register's sheet is "Team KPI Register" and its top section is "Dean KPI 26/27".
  Neither carries KPI anatomy (no unit, numerator, denominator), so neither is a
  KPI here. The app uses Team Initiative / Dean Initiative; "KPI" stays reserved
  for a real measure. The register's own wording is left alone — it is a cited
  source with its own vocabulary.
- **The six Priorities carry KPI anatomy** (measure, target, cadence, owner).
  The canon calls them Priorities; the PMO register calls the same six "Dean
  outcomes" and treats them as KPIs. Both are true: they are the priorities,
  and each is measured. Prefer "Priority" for the entity, "its measure/target"
  for the indicator. On screen a priority reads "Priority 1 · One Shared
  Identity"; `P01` is only the database key.
- **The Outcomes page is illustrative, the rest is not.** Every initiative and
  Dean row is register data. The `/outcomes` page's six cards and milestone
  counts are hardcoded demo structure, and it says so ("Illustrative — format
  only, not CLL results"). A future change replaces it with real measures.
