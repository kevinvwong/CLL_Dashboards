# Design

## Context

See `proposal.md` — Why. What matters here is the shape of what exists.

**The service is live and serving illustrative data.** Eleven commits of history, 197 tests, 27 routes, live at `clldashproto2kwong27.azurewebsites.net`. It is not a greenfield build; every launch action happens against a running service someone may be using.

**Three facts constrain the approach.**

1. **There is no spec store.** `openspec list --specs` reports no specs. The prototype's nine capabilities live only inside the in-flight `add-initiative-dashboard-prototype` change (48/57). The four capabilities in this change are new and standalone.
2. **The Oct 16 view is a static data module, not the database.** `app/oct16_data.py` is generated from `Oct16_Wireframe_Data_Lists.xlsx` and the wireframes; `oct16.html` reads it and nothing else. The prototype's own tables hold goals, initiatives and people — not outcomes, teams or milestones.
3. **The deploy path is undocumented and its exit code lies.** `az webapp deploy` returns 1 while succeeding; the zip is built by an ad-hoc script in `%TEMP%`; there is no rollback.

**Two traps that have already cost time, recorded so they are not rediscovered:**

- `az webapp deploy --type zip` **replaces** `wwwroot` and nothing recreates the SQLite database at startup, so a zip omitting it takes the site down. This happened once this session.
- The App Service gate reads the database to decide whether the site is up, so removing the database fails `/healthz` even though the page content is static.

## Goals / Non-Goals

**Goals**

- Define launch as a judged state with observable criteria, not a deploy event.
- Correct the goal data from the canonical source, and make goal number identity-safe.
- Make the confirmed-versus-illustrative distinction derived from data, so no redeploy can lose it.
- Record a deploy and rollback another person can execute, with success judged by the service.
- Reach the point where the weekly meeting runs from the live service with every owner present.

**Non-goals**

- Porting the prototype onto the Rev2 schema, or moving to Azure SQL.
- Stage 2/3 work: team pages, Power BI, the 35-KPI cascade.
- Entra ID. The passcode gate stays for launch.
- Any change to the Dean's prototype site, which is read-only reference.

## Decisions

### D1: Correct the goal data by re-seeding, not by editing rows
The seed carries goals 3 and 4 transposed and goal 1 truncated. Both `Goals` and `InitiativeGoals` reference goals by `GoalID`, so editing a row's number moves it under a different identity while every initiative tagged to it stays attached to the record — silently re-pointing goal-scoped content.

**Decision:** rebuild the goal rows from the canonical deck (slide 7) against a fresh database, then reload initiatives and their tags through the existing importer. Not an `UPDATE` on live rows.

**Alternative rejected:** editing `GoalNumber` in place. Cheaper, but it makes the identity change invisible in the diff and cannot be verified from the data afterwards.

### D2: The illustrative marker is derived from the data
Today the marker is a constant in `oct16_data.py`. That is a value a person must remember to change, which is exactly what the `confirmed-data` spec forbids.

**Decision:** the marker is computed from whether the served data is the generated illustrative module or confirmed values. Concretely, the data module gains a `CONFIRMED` flag set false in the generated file and true only in a confirmed dataset, and the page renders from it. A deploy that ships the illustrative module reports illustrative; a swap to confirmed values reports confirmed, with no second edit.

**Alternative rejected:** a `DEPLOY_MARKER`-style env setting, hand-set per launch. It works, but it can drift from the data and nothing would detect that.

### D3: The owner is a person or an explicit absence
The PMO workbook's `owner` field is a team — *"Dean + Learning Infrastructure"* — and the register's `Named Owner` column is empty. Neither is a person who can be held accountable or asked for a status.

**Decision:** the data model keeps `owner` as a person, and where none is named the page says so rather than showing a team or a placeholder in the owner position. This follows the user's decision to assume owners arrive on the plan's Oct 9 date; the spec then governs what the page does until they do.

### D4: Deploy success is an observation, not a return code
Measured: `az webapp deploy` exits 1 while reporting *"Build successful"* and *"Starting the site"*, because `az` writes warnings to stderr. Trusting the exit code reports a good deploy as failed; the inverse — trusting a zero exit — would report a bad deploy as good.

**Decision:** the runbook's verification step probes `/healthz` for the revision it just deployed. The command's exit code is recorded as an artefact, never as the verdict.

### D5: Rollback restores both revision and data
A revision-only rollback is not enough: the launch includes a data swap, so reverting the code while leaving the new data yields a state that never existed.

**Decision:** the rollback procedure covers both — restore the previous revision, and restore the previous dataset — and is exercised once before launch rather than written and trusted.

### D6: Launch is judged against the meeting, not the deploy
Every other criterion can pass while the service is still useless to the Dean.

**Decision:** the final go-live criterion is that a real leadership meeting ran from the service with every owner represented. That is the acceptance test, and it is the one that cannot be satisfied by tooling.

## Risks / Trade-offs

- **A deploy takes the site down if the data is mishandled** → the runbook states what the archive must contain and must exclude, and the rollback is exercised first. This has already happened once; it is the change's most likely failure.
- **Re-seeding loses prototype sample data** → acceptable, and intended: the sample data is invented. The importer's dry-run reports what would change before the swap.
- **The goal correction moves content that users may have bookmarked** → goal numbers keep meaning the same goal after correction, which is the point; the risk is to any *external* record of the old (wrong) numbering, which the runbook should list before the swap.
- **A static data module will drift from the wireframes** → the module is generated from them rather than typed, so regeneration is the sync mechanism. The risk is someone editing it by hand.
- **The data-policy position may force launch on sample data** → the `confirmed-data` spec accommodates this: the service stays marked illustrative and says so. Launch is still possible; it is launch *as a demo*, which the marker makes honest rather than hidden.
- **Two live vocabularies** ("priorities" vs "Dean outcomes") describe the same six records → D3 does not resolve it, and it is out of this change's scope. Recorded in the design as a known inconsistency at launch.

## Migration Plan

**Deploy**

1. Build the archive from the current tree, per the runbook. It **must** contain `cll_initiatives.db`, `db/schema.sql` and `db/seed_sample.sql`, because the App Service recreates the database from them and the site fails `/healthz` without it.
2. Set the revision marker app setting.
3. Deploy. Capture the command's output and exit code as an artefact.
4. Probe `/healthz` for the marker just set. That observation, not the exit code, decides success.
5. Walk the gate: `/login` 200, `/` 303 to `/login` unauthenticated, `/oct16`, `/meeting`, `/checks`.

**Data swap (once owners confirm)**

1. Regenerate `app/oct16_data.py` from the confirmed values with `CONFIRMED = True`.
2. Run the importer in dry-run and read the report before committing.
3. Back up the live database via the existing `scripts/backup.py`.
4. Deploy the regenerated module.
5. Verify the illustrative marker has cleared by itself.

**Rollback**

1. Restore the previous revision via the App Service deployment history.
2. Restore the previous database from the backup taken before the swap.
3. Probe `/healthz` and the gate. Confirm the figures match the pre-launch state.
4. Exercised once before launch, not first attempted during an incident.

## Open Questions

- **Is the live service still on a personal `Azure for Students` subscription at launch?** If Georgia Tech has not answered the data-policy question, everything operational stays on sample data and the launch is a labelled demo. This changes what the *launch* means but not the specs, the approach, or the tasks.
- **Does the Dean's prototype's six become the vocabulary, or ours?** It calls them priorities; our pages say outcomes in one place and priorities in another. Deferrable: it changes labels, not behaviour.
- **Is the May 13 deck's six still live?** Recorded in `AUTHORITATIVE_SOURCE.md` §6. Deferrable past October 16, and it governs Stage 2 rather than this launch.
