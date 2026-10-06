# Proposal

## Why

The prototype is functionally complete — 27 routes, 9 capabilities, 197 tests, live on Azure — but it has never been launched as a real product. It serves invented sample data, its goal list is provably wrong, and nothing has been through the operational steps that turn a working demo into something a Dean can rely on for the October 16 deliverable and the weekly leadership meeting that follows.

The reason to do this now is the calendar. October 16 is the first deliverable and the plan's owners-confirm and data-cutoff dates fall before it. The prototype is the only working implementation of the Goal/Priority/Initiative/Person model every source agrees is wanted, and it is further along than either the enterprise package or the Rev2 schema. Launching it is the shortest path to the deadline; rebuilding is not.

## What Changes

- **Launch the whole prototype as a live service**, not the October 16 page alone. The goal lists, priority lists, initiative and person cards, meeting agenda, checks page and admin editing all go live, on confirmed data.
- **Correct the goal data.** The seed carries goals 3 and 4 transposed against canonical Strategy 2035 and goal 1 as a truncated paraphrase. Re-seed from the canonical deck (slide 7) rather than correcting rows in place.
- **Load owner-confirmed values.** The six Dean outcomes' owners and the milestone statuses are currently illustrative. Owners are expected on the plan's Oct 9 date; the page swaps placeholder values for real ones without changing layout.
- **Make the launch repeatable and reversible.** The deploy path is currently a hand-built zip and a manual `az webapp deploy`, with no recorded procedure and an exit code that reports failure while succeeding. Record it as a runbook and give the swap a rollback.
- **Harden the live service for real use.** The remaining pre-launch items from the prototype change: the data-policy position, the operational checks in task group 10, and a first meeting run where the Dean sees updates from every owner.
- **BREAKING** Relabel from "prototype" to "live service" throughout: banners, `APP_ENV` handling, and the synthetic-data labels that exist only because the data is not real.
- **Adopt the Dean's prototype's framing where it is clearer than ours**: it calls the six "priorities"; our pages call them outcomes in one place and priorities in another. One vocabulary, chosen deliberately.

## Capabilities

### New Capabilities
- `live-launch`: what "launched" means for this service — the go-live criteria, the data-swap procedure, the rollback, and the acceptance test that the Dean relies on it in a real meeting. This capability does not exist today, which is why nothing currently distinguishes a working demo from a launched product.
- `goal-data-correctness`: the goal set matches canonical Strategy 2035 in number and wording, and no surface presents a goal whose identity differs from the canonical deck.
- `confirmed-data`: every displayed figure is either confirmed by its owner or visibly marked as illustrative, and the marking cannot be lost in a redeploy or a data swap.
- `deploy-runbook`: a recorded, repeatable deploy and rollback whose success is judged by an observable probe rather than a command's exit code.

### Modified Capabilities

None are modified. The prototype's nine capabilities are **not** in the committed spec store — `openspec list --specs` reports no specs, because they live only inside the in-flight `add-initiative-dashboard-prototype` change. Modifying them here would mean inventing paths under `openspec/specs/` that do not exist, and `openspec validate` would reject them. When that change archives, its specs land in the store and a later change can modify them properly. Until then this change carries its own deltas for the launch-level behaviour the existing surfaces must satisfy.

## Out of scope

- **The Rev2 schema work.** `adopt-rev2-strategy-portfolio-schema` is 48/48 complete and stands on its own. This change does not extend it, port the prototype onto it, or move to Azure SQL.
- **The Stage 2 / Stage 3 programme.** College and team pages on real data, Power BI, the 35-KPI cascade and the six-month build are later work with their own funding and timeline.
- **Option B.** The Infinity drill-in was not selected; it is not built.
- **The May 13 deck's six priorities.** Whether they are live is an open question recorded in `AUTHORITATIVE_SOURCE.md` §6. This change launches on the six that the prototype, the PMO workbook and the wireframes all agree on.
- **Entra ID / SSO.** The passcode-plus-picker gate stays for launch; identity work is bound to the Microsoft migration.
- **Real institutional data beyond what owners confirm.** The data-policy position is recorded, not resolved. If it is unresolved at launch the service stays on sample data and this change says so.
- **Any change to the Dean's own prototype** at `cll-blueprint-2027.wag32002.chatgpt.site`. It is read-only reference.
