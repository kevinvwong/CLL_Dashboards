# Tasks

Every task is scoped to roughly two hours or less, and each group ends with a
check that can be observed rather than described.

## 1. The deploy runbook, recorded before anything is deployed

The deploy path exists only as shell history, and its exit code lies. Record it
first, because every later group deploys with it.

- [x] 1.1 Write `docs/DEPLOY.md` giving the archive's build steps, what it must contain (`app/`, `requirements.txt`, `cll_initiatives.db`, `db/schema.sql`, `db/seed_sample.sql`), and what it must exclude. *Verify: following the document on a clean checkout produces an archive whose entry list matches a recorded listing, with no backslash separators.*
- [x] 1.2 State in the runbook that `az webapp deploy` may exit non-zero while succeeding, and that success is decided by probing `/healthz` for the revision just set. *Verify: the document names the probe and the marker; a reader cannot finish it believing the exit code is the verdict.*
- [x] 1.3 Record the rollback: restore the previous revision from App Service deployment history, then restore the database from the backup taken beforehand. *Verify: the procedure names both halves and the backup command.*
- [x] 1.4 Exercise the rollback once against the live service, deploy forward again, and record what happened. *Verify: `/healthz` reports the expected revision before and after, and the runbook gains a dated note that it was performed.*
- [x] 1.5 List every prerequisite — the `az` path, the credentials file, and the marker convention — with values in `%TEMP%` and paths in the document. *Verify: no credential value appears in the document; a `grep` for the passcode returns nothing.*
- [x] 1.6 **Group check:** hand `docs/DEPLOY.md` to someone who has not deployed this service and have them deploy a no-op revision using only the document. *Verify: they succeed without asking a question, and the service reports the revision they set.*

## 2. Goal data correctness

Goals 3 and 4 are transposed and goal 1 is truncated. Correct from the canonical source, by re-seeding rather than editing, because a goal's number is its identity.

- [x] 2.1 Extract the five goals and their canonical wording from `CLL-strategy-2035-presentation.pptx` slide 7 into a source file under `ospec/db/`, recording the slide as provenance. *Verify: the file holds five goals numbered 1–5, and its text matches the deck character for character including non-ASCII.*
- [x] 2.2 Rewrite the goal rows in `ospec/db/seed_sample.sql` from that source, leaving initiative and tag rows untouched. *Verify: a diff shows only goal rows changed; `grep` finds no goal title that is a paraphrase or blank.*
- [x] 2.3 Rebuild the sample database from the corrected seed and confirm the tagged initiatives are still attached to the same goals. *Verify: the count of `InitiativeGoals` rows is unchanged, and each initiative's goal set is identical before and after.*
- [x] 2.4 Add a test asserting goal number and canonical wording agree for all five, reading the expected text from the source file rather than duplicating it. *Verify: the test fails if any goal's number is changed; proven by changing one number and watching it go red.*
- [x] 2.5 Add a test asserting no two goals are transposed, by checking that each number's stored title matches the source's title for that number. *Verify: the test fails against the pre-correction seed and passes after, and both runs are recorded.*
- [x] 2.6 Document the change in `ospec/db/README.md` or equivalent, stating what was wrong, what the correct source is, and that goals are re-seeded rather than edited. *Verify: the document names the transposition explicitly.*
- [x] 2.7 **Group check:** walk `/goals/3` and `/goals/4` on a locally served build and confirm each names the goal the canonical source assigns that number. *Verify: the two pages are not transposed, checked against the source file rather than from memory.*

## 3. The illustrative marker, derived from the data

The marker is a constant today, so a redeploy or a swap could leave it wrong. Make it follow the data.

- [x] 3.1 Add a `CONFIRMED` flag to `app/oct16_data.py` defaulting to false, and set it true only in a confirmed dataset. *Verify: the flag exists in the generated module and is false in the committed one.*
- [x] 3.2 Render the illustrative status text from that flag in `oct16.html` rather than from the `DATA_STATUS` constant. *Verify: with the flag false the page says illustrative; flipping it true locally clears the statement with no template edit.*
- [x] 3.3 Extend the generator so `CONFIRMED` is set by whether it was run with confirmed values, not hand-edited. *Verify: regenerating from the wireframe source yields false; a unit test proves a confirmed input yields true.*
- [x] 3.4 Add a test asserting the marker survives a redeploy: build the page from the committed data twice and assert the status text is identical. *Verify: the test fails if the flag is hard-coded in the template.*
- [x] 3.5 Add a test asserting an unknown figure is shown as unknown and not as zero, covering the no-update case on both the outcome cards and the person card. *Verify: both surfaces show a distinct unknown state; the test fails if either renders an empty bar.*
- [x] 3.6 Add a test asserting an unnamed owner renders as an explicit absence and never as a team or a role string. *Verify: the test fails against a team-valued owner.*
- [x] 3.7 Add a placeholder for a withheld owner name, distinct from both a real name and an unnamed owner, and test that it is treated as unconfirmed. *Verify: the placeholder renders as one, and the item is not reported as having a confirmed owner. Per the user's decision of 2026-10-07, real names are withheld until the data-policy question is answered, so every owner position carries a placeholder at launch.*
- [x] 3.8 **Group check:** deploy with the flag false and confirm the live page states its figures are illustrative and shows placeholders in every owner position. *Verify: the live page's status text says so and no real name appears; both were set by the data, not by an app setting.*

## 4. Data swap, once owners are named

Owners are expected on the plan's Oct 9 date. This group is written so it can run the moment they are.

- [ ] 4.1 Add a documented path to regenerate `app/oct16_data.py` with owner names and confirmed statuses, taking the values as input rather than requiring edits to the module. *Verify: running it with a sample owners file produces a module whose `CONFIRMED` is true and whose owners are those names.*
- [ ] 4.2 Add a dry-run check that reports what the swap would change — outcomes gaining owners, statuses changing — before anything is deployed. *Verify: running it against the illustrative data reports every difference and changes nothing.*
- [ ] 4.3 Add a test asserting the swap does not alter layout: the same six cards, the same 19 data rows, the same section headings, before and after. *Verify: a structural comparison of the rendered page pre- and post-swap differs only in values.*
- [ ] 4.4 Take a live database backup with `scripts/backup.py` immediately before the swap and record its filename. *Verify: the backup file exists and its timestamp precedes the deploy.*
- [ ] 4.5 Perform the swap against the live service once a real owners file exists, then verify the illustrative marker has cleared by itself. *Verify: the live page shows named owners and no longer says illustrative, with no app setting changed.*
- [ ] 4.6 **Group check:** confirm the live page's six outcomes each name a person and that every status shown is one an owner confirmed. *Verify: no cell reads `[name]`, and no status is invented — checked against the owners file.*

## 5. Meeting readiness

The acceptance test for the whole change: the Dean reads a real meeting from the service.

- [ ] 5.1 Confirm the meeting page's attention list, changes list and print layout work against the swapped data. *Verify: all three sections render, and printing produces the agenda without navigation.*
- [ ] 5.2 Confirm the owner-update path works live: an owner signs in, posts an update, and it appears on their initiative and on the meeting page. *Verify: the posted update is visible at both places without a reload trick.*
- [ ] 5.3 Confirm the checks page is empty or explains itself against real data. *Verify: `/checks` lists only genuine issues, and a clean dataset shows none.*
- [ ] 5.4 Send the URL, the passcode separately, and a short how-to to each named owner. *Verify: each owner has both the URL and their own sign-in details; no passcode is sent alongside the URL.*
- [ ] 5.5 **Group check:** a real leadership meeting runs from the live service with every owner due to report appearing with an update. *Verify: the meeting page shows an update from every owner, observed during the meeting itself.*

## 6. Integration and launch decision

Cross-cutting checks only. Each earlier group landed its own tests and documentation.

- [ ] 6.1 Run the whole suite and both validations. *Verify: all tests pass and `openspec validate --all --strict` exits 0.*
- [ ] 6.2 Verify the full gate on the live service: `/login` 200, `/` 303 to `/login` when unauthenticated, `/healthz` reports the current revision, `/robots.txt` disallows all. *Verify: each observed on the deployment, with the responses recorded.*
- [ ] 6.3 Verify the data-policy position and record it. If Georgia Tech has not cleared personal-subscription hosting, state in the launch record that the service runs on sample data and is a labelled demonstration. *Verify: the launch record states which it is, with a date; it does not leave the reader to infer it.*
- [ ] 6.4 Judge the launch against the go-live criteria in `live-launch/spec.md`, recording each as observed or unmet. *Verify: every criterion has an observed result, and any unmet one is named rather than averaged away.*
- [ ] 6.5 Record the launch decision and its basis in the change's tasks or a launch note. *Verify: a reader can tell from the artefact whether the service is launched, on what evidence, and what remains unproven.*
