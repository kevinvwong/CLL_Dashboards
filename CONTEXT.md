# CONTEXT

The domain vocabulary for the CLL Initiative Dashboard. A glossary, not a spec:
terms here name *what things are*, not how they are built.

## Why this file exists

The prototype this dashboard grew from called the 29 rows below "KPIs". They are
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

> **Do not call a Major Initiative a KPI.** If a row has no measure and no
> target, it is not an indicator.

**Major Initiative** — one of the 29 bodies of work the College will execute,
aligned to one or more Strategy 2035 goals. Identified `MI-001`..`MI-029`. A
Major Initiative is *work*; a KPI is a *measurement*. A Major Initiative names
the smaller initiatives that deliver it.
*Source:* the canon workbook's `Initiatives` sheet (header "Major Initiatives";
Quality Check `Initiatives 29/29 PASS`). Columns: Initiative ID, Initiative
Name, Source Area, Strategy Alignment, Status, Validation Category — note the
absence of any measure or target.

**Team** — one of the four organizational units accountable for work:
Learning Experiences, Learning Ecosystems, Learning Infrastructure, Learning
Futures. A team is an accountability axis, distinct from a source area.

**Source Area** — the register area a Major Initiative was filed under (e.g.
"Content & Product Strategy"). A source area is where something was *recorded*;
a team is who is *accountable*. The two are different axes and are not
interchangeable.

**Initiative** (unqualified) — an entry in the dashboard's sample demonstration
population (the `Initiatives` table), with a level (Dean / D-1), an owner, and
progress updates. Deliberately separate from a Major Initiative: these are
invented demo records, explicitly not governance-approved. When the word
"Initiative" appears alone in the UI it means this demo population; the canon's
29 are always "Major Initiatives".

## Known tensions

- **Two populations are called "initiative".** The canon's 29 Major Initiatives
  and the dashboard's 22 sample Initiatives are different things. The qualifier
  "Major" is load-bearing: without it the two are ambiguous.
- **The six Priorities carry KPI anatomy** (measure, target, cadence, owner).
  The canon calls them Priorities; the PMO register calls the same six "Dean
  outcomes" and treats them as KPIs. Both are true: they are the priorities,
  and each is measured. Prefer "Priority" for the entity, "its measure/target"
  for the indicator.
