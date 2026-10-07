# Progress log — CLL Initiative Dashboard

A running, dated record of what actually changed. **Newest first** — add each
day's entry at the top, under "Entries". Ground every line in evidence (a commit,
a test run, a deployed marker); never record intended work as done.

**How to add an entry**

```
## YYYY-MM-DD — <one-line theme>

**Shipped**
- <outcome> (`<short-sha>`)

**Verified**
- <test count / probe / marker>

**Decided**
- <decision, and where it is recorded>

**Open / next**
- <open item>
```

Rules: one bullet = one outcome, not an activity. Cite the commit. If something
is unverified, say "unverified". Never print a credential value — cite the file
and key only.

---

## Entries

## 2026-10-07 — Register canon merged, layers renamed, repo assessed

**Shipped**
- The two competing initiative models **merged into one** on the register's model;
  the five prototype tables dropped and the diary moved onto the 29 (`e95441e`).
- Read layer rewritten to the register model (`100b010`); writes retargeted
  (`55120cd`); permissions resolve on the register, `is_dean` by title (`86a26ce`);
  routes collapsed, `/initiatives/*` → `/major-initiatives/*` (`d3b6651`).
- Register seeded end-to-end: owners, team moves, the Dean layer, co-owners
  (`d37415d`), plus the `/changes` reader and change-log `EntityType` fix
  (`9ca3a34`, `397f36c`).
- **Layer rename**: Major Initiative → **Team Initiative**, Dean Priority →
  **Dean Initiative**, across schema/routes/code/docs/tests (~2,000 occurrences)
  (`ae4db5d`, `dba5b17`, `86bf60d`).
- Priorities spell out on screen: **"Priority 1 · One Shared Identity"** (`1fe1611`).
- Dean layer moved to its own page, `/dean-initiatives`, listing the **61**
  Team-Initiative roll-up chips (`f24cc5d`, then the roll-up query).
- **Removed the false "invented / not governance-approved" labels** once the
  register was confirmed approved (`8cff6fb`).
- Accessibility pass: bar contrast, breadcrumb underline, real-anchor rows
  (list semantics), 320px overflow (`15df90b`).
- Overview de-duplicated; honest "no progress reported yet" health line (`cd6d988`).
- `Target.card_id` guard fix (`844c619`).
- Repo + Planner assessment written (`0afeea5`).

**Verified**
- Suite **551 passed, 1 skipped**; new axe + provenance guards green.
- Deploy markers recorded in `docs/ops/LAUNCH_RECORD.md`.

**Decided**
- **Environment policy**: local = dev, Azure = production; no deploy until the
  user declares a checkpoint (`b14015b`, `docs/ops/DEPLOY.md`).
- Register is canon and (confirmed) **approved**; the Outcomes page keeps its own
  "Illustrative" marker because it is separate, hardcoded data.

**Open / next**
- Credential leak: `docker-compose.yml` tracked; `.env` in history. Rotation +
  purge pending user approval (see the assessment's §4).
- Entra auth / roles / admin / ops: not implemented (Phase 1+).

---

## 2026-10-06 — Design system, blueprint redesign, interconnection, Hive restyle

**Shipped**
- Design-system foundation (tokens, components) and the whole blueprint redesign
  in six groups, archived with six published specs (`a546fdf`…`c9899c9`).
- Organizational layer live: 4 teams, 5 source areas, 29 rows (`87f019a`).
- The KPI → Goal edge, and the interconnection redesign that cut the overview
  (`3d2154e`, `2b8f188`).
- Canon rows matched to prototype rows **by name, not position** — fixing eight
  shifted targets (`2b59feb`).
- Repository restructured to a flat root; OpenSpec removed; CI retargeted to
  `main` (`df2ac05`, `1f1c0cb`, `64a0894`).
- Hive restyle applied (`c2702f5`); GT logo added to the app bar (`673acc8`).
- Staleness ages read on one clock (UTC) — the two-clock bug fixed (`56b896e`).
- Browser-analysis fixes in batches; wayfinding, Outcomes, drawer, vocabulary
  (`2e2d9c6`…`026eafd`).
- Clean, reproducible sample database committed (`d437c52`).

**Verified**
- Suite green after each batch (count grew through the day; not recorded here).

**Open / next**
- Rename the 29 from "KPIs" (done 10-06 in `6e21cc5`).

---

## 2026-10-05 — Prototype built end to end

**Shipped**
- Initial commit: FastAPI/Jinja2/HTMX prototype with Dockerfile, compose, `.env`,
  CI workflow (`4ee6d3e`).
- Dashboard built end to end (`5985f18`); `APP_ENV` banner, backup retention, and
  the intake Feeds/Percent/Status columns (`af6e1c6`).
- Five flow defects fixed reviewing schema against navigation (`e54e13c`).

**Verified**
- Unverified at this date — no test-run count recorded.

**Open / next**
- Move off the prototype model toward a designed system.

---

## Standing state (update when it changes)

- **Production:** `clldashproto2kwong27.azurewebsites.net`, marker
  `labels-20261007T123612Z` (checkpoint). Deploys only on a declared checkpoint.
- **Local dev:** `run-dashboard.cmd` → `http://127.0.0.1:8000`.
- **Tests:** `python -m pytest` — **551 passed, 1 skipped** (stop the dev server
  first, or `test_build_is_reproducible` fails spuriously).
- **Known risks:** credential leak (§4 of the assessment); no Entra auth; no
  monitoring; F1 stop-quota availability.
