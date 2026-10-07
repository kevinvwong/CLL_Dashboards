# Launch record — CLL Initiative Dashboard

Date: 2026-10-06
Change: `launch-initiatives-dashboard-live`
Author: the agent, on the user's direction.

This note is the launch record the change's tasks 6.3–6.5 require. It states
**whether the service is launched, on what evidence, and what remains unproven.**
It is written to be read cold: nothing here should need inferring.

## The decision: NOT LAUNCHED

The service is a **labelled demonstration on sample data.** It is not a launched
institutional dashboard, and it must not be presented as one at a leadership
meeting.

Two independent reasons, each sufficient on its own:

1. **It carries no real data.** The content module reports
   `Illustrative — format only, not CLL results`, `CONFIRMED = False`, and every
   outcome reads `[no owner named]`. No owner has confirmed a figure.
2. **It is not reliably reachable.** The live App Service plan is stopped by its
   own quota (see "The deployment is down", below). A service that answers `403`
   is not launched whatever its content says.

## 6.3 — the data-policy position (verified, not assumed)

**Georgia Tech has not cleared personal-subscription hosting.** The live
environment is Azure App Service on the author's own `Azure for Students`
subscription, outside the Georgia Tech tenant. The question in the prototype's
design.md Open Questions is **partially answered at best**, so:

> The service runs on **sample data only** and is a **labelled demonstration**.
> Every page carries the sample-data bar and the footer marker; the outcomes page
> states the figures are illustrative and no owner is named.

This is the interim position the change anticipated. It is stated here with a
date so it is not inferred.

## 6.4 — the go-live criteria, each judged

From `specs/live-launch/spec.md`. Every criterion is recorded as observed or
unmet. None is averaged away.

| Criterion | Result | Evidence |
|---|---|---|
| Goal data matches the canonical strategy | **Met in code, unproven live** | The goal-correctness tests pass against the sample database; the deployed revision predates them |
| Every displayed figure is confirmed or marked | **Met** | `data_status()` reports `Illustrative — format only, not CLL results`; no owner is named, and the page says so |
| The weekly meeting ran from the service | **UNMET** | No meeting has run from it; the service has been down on quota and carries sample data |
| The live data is the live data | **UNMET** | There is no live data. The database holds sample rows only |
| Rollback returns the previous state | **Met** | The rollback was exercised against the live service (see `docs/DEPLOY.md`, 1.4): broken archive → 503, restore → 200 |
| The data swap is reversible | **Met** | `scripts/swap_oct16_data.py` backs the database up before writing; the rollback was exercised locally and the backup restored cleanly |
| Illustrative data announces itself | **Met** | The sample-data bar and the footer marker render on every page |
| Confirmed data does not claim more than it is | **Met** | The marker distinguishes illustrative, partly-confirmed, and confirmed; a no-name file is refused rather than claimed |

**Three of eight criteria are unmet**, and they are the three that make a launch
a launch: real data, a real meeting, and a live service.

## 6.2 — the gate on the live service (observed)

Not run this session: the app returns `403 This web app is stopped`, so there is
no gate to walk. The reason is below.

## The deployment is down, and it is the free tier

Measured 2026-10-06 19:58Z:

- The plan `cll-dash-proto-plan` is **F1 Free**.
- `WPStopRequests` — its hourly stop-request counter — reads **80 / 15**.
- The plan state is `QuotaExceeded` and **both** apps on it answer `403`.
- `alwaysOn` is not available on Free, so the app idles, stops, and each cold
  start spends from the same counter.

This is why every deploy attempt has failed to stay up: the deploy is itself a
stop request, so the plan stops and the counter moves further out. It is a
platform limit, not a code defect.

## What is proven, and what is not

**Proven:** the suite (460 tests) and both validations (15 items) pass; the goal
data matches the canonical strategy; the illustrative marker is honest; rollback
and the data swap are reversible.

**Not proven:** that the service stays reachable; that a leadership meeting can
run from it; that any real figure has been confirmed by its owner.

## To launch it, in order

1. **Leave F1**, or the quota will keep stopping it (a paid tier enables
   `alwaysOn` and removes the stop-request cap).
2. **Clear the data-policy question**, or keep it explicitly on sample data.
3. **Run the data swap** with real owner names, then confirm the marker clears.
4. **Run the Wednesday meeting** from the service, which is the criterion no
   deployment alone satisfies.
5. Re-run tasks 6.1–6.5 and record the result here.

Until 1–4 hold, this service is a demonstration.

## 2026-10-07 — Register as canon; owners, team moves, and a Dean layer

`Initiative Dashboard Register.xlsx` (supplied 2026-10-07, last authored by
`Smith, Elizabeth C`, produced by Microsoft Excel Online) supersedes the earlier
canon workbook for the Major Initiatives. It is the first source to carry real
**Named Owner** values, descriptions, a Goals 1-5 alignment matrix, and a Dean
layer. It was adopted on the user's instruction: **"register is canon and
overwrites."**

**Team reassignments (four rows moved to _Learning Ecosystems_):**

| Major Initiative | Was | Now |
|---|---|---|
| Growth Engine Readiness | Learning Experiences | Learning Ecosystems |
| Strategic Partnership & Revenue Growth | Learning Experiences | Learning Ecosystems |
| Geographic Expansion | Learning Experiences | Learning Ecosystems |
| Asset Utilization | Learning Infrastructure | Learning Ecosystems |

Team totals after the move: Learning Ecosystems 6, Learning Experiences 10,
Learning Futures 6, Learning Infrastructure 7 (29 in total).

**Titles reworded by the register (five):** MI-024, MI-025, MI-026, MI-027,
MI-029 now carry the register's tighter wording.

**Named owners (real, replacing placeholders):** Bill Gaudelli (Dean),
Mario Herane (Learning Ecosystems), Tim Jacobbe (Learning Experiences),
Meltem Alemdar (Learning Futures), Elizabeth Smith (Learning Infrastructure).
The register names Learning Futures' six rows with two people in one cell
("Meltem Alemdar/Grace Flavin"); Meltem Alemdar is the accountable lead
(`OwnerID`) and **Grace Flavin** is held in `MajorInitiativeCoOwners`, so neither
is lost.

**Dean Priorities layer (new):** 11 rows in `DeanPriorities` — FY26 (3, all
complete) and FY27 (8, in flight) — each with a 0-100 `PercentComplete` scaled
from the register's 0-1 value. Presented in the app as "Dean Priorities". 61
Major-Initiative-to-Dean-FY27 links are held in `MajorInitiativeDeanLinks`.

**Change log:** the `AuditLog.EntityType` derivation was corrected — it was keyed
by entity but looked up by the action's first word, so every goal, priority, tag
and link edit was recorded as an "Initiative". Two indexes were added and a
readable admin **`/changes`** page now lists the log.

**Still not launched.** This remains a labelled demonstration: hosting is on the
author's personal `Azure for Students` subscription and the GT data-policy
position is unchanged. The register's owners are the register's named leads, not
institutionally confirmed ownership.

## 2026-10-07 — Deployed: register canon, Dean layer, change log

**Marker `register-20261007T094057Z` confirmed live on the first `/healthz`
poll.** The register work is now serving at
`https://clldashproto2kwong27.azurewebsites.net`.

Verified live after deploy:

| Check | Result |
|---|---|
| `/healthz` | 200, marker matched on the first poll |
| `/robots.txt` | 200, `Disallow: /` |
| `/login`, `/` (anon) | 200; 303 to login |
| `/whoami` picker | lists Bill Gaudelli, Meltem Alemdar, Grace Flavin |
| Home | Dean Priorities FY26/FY27 with percent bars; teams 6/10/6/7 |
| `/major-initiatives/MI-002` | description and "Contributes to" chips render |
| `/changes` | 200 for the admin (Kevin); 403 for the Dean (not an admin) |

The archive shipped 70 entries (was 68): `db/seed_register.sql` and
`db/seed_canon_links.sql` were added to the archive manifest, because a rebuild
from the archive would otherwise omit the Dean layer, the owners and the four
team reassignments — the same class of defect `seed_team_layer.sql` had until
2026-10-06.

Deploy caveats observed: the F1 plan's `WP stop requests` read 0/15 before the
deploy (reset 14:00Z), so no quota risk; `az webapp deploy` reported
`RuntimeSuccessful` and this time exited 0.

**Still not launched in the governance sense.** This remains a labelled
demonstration on sample data — the banner reads "Sample data — these initiatives
are invented for this prototype". The GT data-policy position is unchanged, and
the owners are the register's named leads, not institutionally confirmed.

## 2026-10-07 — Deployed: the two initiative models merged

**Marker `merge-20261007T114347Z` confirmed live on the first `/healthz` poll.**

The database held TWO initiative models and the home showed both at once
("22 initiatives tracked" beside "29 Major Initiatives"), which read as a
contradiction. The register is canon, so they are merged onto its model:

- The five prototype tables (`Initiatives`, `InitiativeGoals`,
  `InitiativePriorities`, `InitiativeLinks`, `ProgressUpdates`) are **dropped**.
- The progress diary moves to `MajorInitiativeUpdates`, on the register's 29.
- `repo.py`, `auth.py`, `queries.py` and every route now read/write the register
  model, keyed by `MIId`.
- `/initiatives/*` **308-redirects** to `/major-initiatives/*`; the interactive
  card (drawer, update form, edit forms) is now the register's page.
- The 24 prototype diary rows were discarded, not migrated: every one named a
  sample initiative, and none named a real Major Initiative.

Verified live after deploy:

| Check | Result |
|---|---|
| `/healthz` | 200, marker matched on the first poll |
| Home | **29 initiatives tracked** (one portfolio number, was 22-vs-29) |
| Stat tiles | 29 / 6 / 4 / 29 / 21 |
| `/initiatives` | 308 to `/major-initiatives` |
| `/major-initiatives`, `/{mi_id}` | 200 |
| `/changes` (admin) | 200 |

Also fixed in this change: `scripts/import_xlsx.py` and `scripts/make_template.py`
retargeted to the register model (the importer wrote to the dropped tables and
would have failed); `vw_DataChecks` dropped its "No progress update yet" check
(an initiative with no diary is the normal state, and the importer refuses any
import that leaves a check outstanding, so that check would have blocked every
import); and `/major-initiatives/new` was declared after `/{mi_id}` and 404'd.

**Suite: 546 passing, 0 failing. Database byte-reproducible.**

**Still not launched in the governance sense.** This remains a labelled
demonstration on sample data - the banner reads "Sample data - these initiatives
are invented for this prototype". The GT data-policy position is unchanged.

