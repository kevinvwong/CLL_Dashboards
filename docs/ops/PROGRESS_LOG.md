# CLL Initiative Dashboard — progress log

A plain-English record of what changed on the dashboard, day by day. It is generated from the project's history, so it always matches the work that actually happened. Newest day first.

> **Newest first.** This page is produced by `scripts/build_progress_log.py` — do not edit it by hand; the next run overwrites it.

## How to read this

Each line is one change to the dashboard, under a plain heading. The wording is the change's own, kept as written so the record stays accurate; a few lines name technical things (a file, a screen, a feature) because that is what the change was about. The glossary below covers the domain words; you do not need the technical ones to follow the day-to-day story.

## At a glance

- **5** days of work recorded, **189** changes in total.
- Most recent day: **Friday 09 October 2026**.
- Across all days: 66 what we added; 37 what we fixed; 5 appearance and design; 24 behind the scenes; 13 quality and testing; 27 documentation; 17 more changes.

## Words used on this page

- **Register** — the official spreadsheet of the College's approved work that this dashboard shows
- **Team Initiative** — one of the 29 bodies of work the College will deliver
- **Dean Initiative** — one of the top-level pieces of work owned by the Dean
- **Priority** — one of the six yearly focus areas (the dashboard shows 'Priority 1', 'Priority 2', ...)
- **Goal** — one of the five Strategy 2035 goals the work aligns to
- **Dashboard** — the web page this log describes
- **Prototype** — an early, non-final version used to agree the design

---

## Friday 09 October 2026

**What we added**

- Show the team, not the title, everywhere a person is named

**What we fixed**

- Chown /app after the copies, so the app can write its database

**Behind the scenes**

- Remove the per-person PIN; refactor(copy): one term per thing
- Stop the landing page repeating itself

**Documentation**

- Bring the Dean+COO meeting record into the repo, in full


## Thursday 08 October 2026

**What we added**

- Implement Clerk behind the authenticate() seam
- Wire Clerk for Entra SSO, with a chrome-free pre-auth surface
- Give the Clerk sign-in a smooth, on-brand surface
- Separate executive authority from routine updates (DR-23)
- Reconcile role names to the roster and add the Strategic Operations roster
- Support a second (alias) email per user, so either address links
- Apply the Rev2 schema and seed it from the app data
- Add the store seam (DB_PROVIDER: sqlite | mssql)
- Port the home/taxonomy reads to Rev2 (DB_PROVIDER=mssql) + the dialect seam
- Complete the reconciliation - carry the four app layers Rev2 lacked
- Port the cascade + index reads to Rev2 (adopt-rev2-store group 3)
- Port the team-initiative layer to Rev2 (adopt-rev2-store group 4)
- Port the card + priority + edit reads to Rev2 (adopt-rev2-store group 5)
- Port the write path to Rev2 + close adopt-rev2-store (groups 6-7)
- Port the remaining six surfaces to Rev2 (rev2-remaining-surfaces)
- Port the authentication surface to Rev2 (port-auth-to-rev2)

**What we fixed**

- Sign out through clerk-js, not a cookie delete
- Serve a favicon instead of 404ing on every page
- Commit the rebuilt database with the six canonical roles
- Stop a rebuild wiping environment-specific rows (Clerk links)
- Copy docs into the image and add a .dockerignore

**Behind the scenes**

- Add a read-only host diagnostic script
- Pin line endings so a shell script stays LF for a Linux clone

**Documentation**

- Add the stack specification for handoff and provisioning
- Reframe the Azure request as a forward-looking two-environment build
- Correct the live region in the repo assessment (westus -> northcentralus)
- Name the six application roles in the provisioning request
- State the Entra role boundary and the role-assignment licensing question
- Record the user/role roster and the Clerk provisioning
- Record each person's two addresses (account + alias)
- Record the Rev2 identity model in the deploy runbook
- Record the rev2-store production deploy
- Record that Clerk is development-only and Entra is production


## Wednesday 07 October 2026

**What we added**

- Add a second-pass review prompt (post-fix)
- Add Task 6 (change log: EntityType fix, indexes, /changes reader)
- Add Dean Priorities layer, register columns, AuditLog indexes
- Generate the register seed (owners, teams, Dean layer, co-owners)
- Dean Priorities section, MI contributes-to chips, and a /changes reader
- Ship the register seeds in the deploy archive; record the 2026-10-07 deploy
- Merge to one initiative model; add the diary, drop the prototype tables
- All writes target the register model
- Permissions resolve on MajorInitiatives; is_dean by the register's title
- All reads source the register model
- Collapse /initiatives/* onto /major-initiatives/*; the card is one surface
- Spell out 'Goal N' in prose; add status glyphs for colour-blind/print readers
- Move the 11 Dean Priorities to /dean-priorities; home keeps a one-line roll-up
- Priorities read 'Priority 1 · One Shared Identity'; remove orphaned warn tokens
- Generate the progress log from git, written for a non-technical reader
- Show the last push and deploy time as a discreet stamp
- Add the Milestones model, priority outcome state, and dataset provenance
- Collect milestones and outcome state by workbook, and confirm on import
- Read the Outcomes page from the Milestones model, not the module
- Give goals and teams a keyed colour and icon, with a legend
- Nav icons, stat-tile proportion fill, and the Dean FY timeline bar
- Milestone rings, milestone-chip icons, and cascade rails
- All six blueprint moves, all respecting reduced motion
- Close the picker escalation with a PIN, add local roles, and extend the change log
- A persistent left rail with a mobile tab bar
- An in-app documentation set, single-sourced from docs/*.md
- Split the four views of the portfolio onto their own pages
- Key priorities by (plan year, code) so a second year is representable
- Be specific about 2027, and make the year a first-class concept
- One shared card component across the goal, team, person and priority cards

**What we fixed**

- Fix the write-path forms and the re-review's new findings (N1-N5, N8)
- Correct the re-review file
- P01 'as a College' and P06 curly apostrophe; correct at the generator
- Retarget import_xlsx to the merged model; add a diary fixture
- Declare /major-initiatives/new before the {mi_id} route
- .bar-fill is a span, so make it display:block; Dean progress bars were drawn empty
- Stop the overview counting the same set twice; honest health line when the diary is empty
- Add Target.card_id so admin_for routes stop indexing a maybe-None card
- Bar contrast, breadcrumb underline, real-anchor rows (list semantics), 320px overflow
- The register is approved, so remove the 'invented / not governance-approved' labels
- Alias the intermediate /major-initiatives and /dean-priorities names
- Progress log ignores its own refresh commits, so it can stay current
- Priority chips render their real colour, not var(var(...))
- Render the nav and goal SVGs, not their escaped text
- Priority chips keep a readable label over their swatch
- Let the content column shrink, and fix the rail item contrast
- Rebuild the shipped database for the multi-year schema

**Appearance and design**

- Register as canon and the Dean Priorities layer
- Merge the two initiative models (register-driven)

**Behind the scenes**

- Record the 2026-10-07 merged-model deploy
- Rename the layers - Team Initiative / Dean Initiative
- Finish the layer rename in CONTEXT and the import scripts
- Ship the docs the in-app guide renders

**Quality and testing**

- Sign in with the canonical owner names
- Retarget the suite to the merged model (mechanical pass; semantic migration remains)
- Migrate cards to the merged model; drop the empty-diary data check
- Migrate meeting/checks to the merged model; checks link by MIId
- Migrate cascade views to the merged model
- Migrate admin + lists to the merged model; fix edit-links template gate
- Repoint nav destinations to /major-initiatives
- Fix repo kwarg call sites and duplicate-code fixture
- Migrate drawer, search, home to the merged model
- Migrate intake to the merged model; importer keys on MIId or Code
- Finish the flows/intake/synthetic migration; fix edit-result redirect
- Complete the merged-model migration - suite green (546 passing)
- Guard the shipped database against a schema change without a rebuild

**Documentation**

- Azure provisioning requirements and IT request
- Mark register-canon tasks complete
- Add future Azure needs (Entra, managed identity, domain) to the provisioning request
- Record the local=dev / Azure=production policy and the production checkpoint
- Update the glossary for Team Initiative / Dean Initiative and the roll-up
- Repo and Planner assessment (2026-10-07)
- Planner reconciliation - one rename, all platform tasks stay open
- Power Pages feasibility brief
- File the Visual Enhancement Blueprint with a reconciliation note
- Plan the enhancement + model work and record the auth decisions
- Record the enhance-20261007T195252Z checkpoint
- Record the shell-guide-20261007T203634Z checkpoint

**More changes**

- Widen the layout to a dashboard cap, and give search its combobox roles
- Spec self-review: name all three edge sets the register seed writes
- Register as canon and Dean Priorities layer
- Rebuild from the register; record team moves, owners and the Dean layer
- Merge the two initiative models
- Define the progress percent, add the Outcomes roll-up and the dot/banner notes


## Tuesday 06 October 2026

**What we added**

- Ship the October 16 deliverable: the six Dean outcomes by milestones
- Add the October 16 data-swap path, with a dry run and a backup
- Add the local run steps to the README, and make build_db.py reproducible
- Add the blueprint-redesign change, superseding overhaul-ui-ux-navigation
- Add the design-system foundation: tokens, components, and behaviour
- Apply group 1 of blueprint-redesign: the visual system
- Apply group 2 of blueprint-redesign: the blueprint home
- Apply group 3 of blueprint-redesign: cascade drill-downs and indexes
- Apply group 4 of blueprint-redesign: the initiative drawer
- Apply group 5 of blueprint-redesign: navigation, coverage, meeting, outcomes
- Add the organizational layer: 4 teams, 5 source areas, 29 team KPIs
- Apply group 6 of blueprint-redesign: verification, and complete the change
- Add the KPI -> Goal edge from the canon register
- Add run-dashboard.cmd to launch the app from the command line
- Scaffold the engineering-skills configuration
- Add the design-system brief for Claude
- Add the official GT logo to the app bar (Hive handoff 3)

**What we fixed**

- Fix X-Robots-Tag missing on the access-gate redirects, and test the local banner
- Correct the goal data from the canonical deck, and fix two latent bugs it exposed
- Refuse a deploy archive that carries two databases
- Refuse a deploy archive that ships a credential file
- Fix the six verified UI defects, and land the UI/UX change
- Restore the superseded-change zip, deleted by an errant glob
- Harden the design-system brief after simulating the handoff
- Fix four usability defects found in review
- Free the port before starting, safely
- Match canon rows to prototype rows by name, not position
- Fix the clear defects from the browser analysis
- Fix wayfinding: breadcrumbs, /teams, nav highlighting

**Appearance and design**

- Interconnection redesign (canon data edges, then UI)
- Restyle the dashboard with Hive
- Style the drawer's controls and fix two data encodings (#11, #18, #15)

**Behind the scenes**

- Follow the wireframes: scope block, data table, trade-offs, owner line
- Read the Dean's prototype, and correct the priority claim I had wrong
- Record the deploy runbook and exercise the rollback
- Derive the illustrative marker from the data, and give owners three states
- Deepen six dashboard modules behind smaller interfaces
- Record apply progress for deepen-dashboard-modules (33/34; 7.2 gated on the F1 quota reset)
- Replace the hero stage with a portfolio dashboard, surfacing every field
- Archive blueprint-redesign and publish its six specs
- Archive the two abandoned scaffolds and the superseded change zip
- Call the 29 Major Initiatives, not KPIs
- Relocate the app out of OpenSpec and remove OpenSpec
- Restructure to a flat repo root and remove dead weight
- Retarget CI to the renamed default branch
- Read staleness ages on one clock (UTC), the clock the data is written with
- Drop two vestigial Major Initiative fields carried from the prototype
- Commit the clean, reproducible sample database

**Documentation**

- Describe the intake template's real columns, and fix a message that said the opposite
- Write the authoritative source, reconciling four bodies of work
- Write the Dean's decision brief for the October 7 option meeting
- State the goal at the top of the design-system brief

**More changes**

- Adopt Revision 2 as the Strategy Portfolio target schema
- Rank the meeting attention list by severity and honour the whole requirement
- Option A chosen: the page now reads as the deliverable, not a candidate
- Complete the remaining work, and record what cannot be completed
- Interconnect the goals, teams and KPIs; cut the overview; ice the meeting
- Require seed_team_layer.sql in the deploy archive
- Clean up the Outcomes page for the Dean (#2, #4, #12, #3)
- One vocabulary, one label, a health read, and a type fix (#6, #7, #8, #19)
- Polish, and record the analysis and its workflow (#22, #23, #27)


## Monday 05 October 2026

**What we added**

- Build the initiative dashboard prototype end to end
- Add APP_ENV banner, backup retention, and the intake Feeds/Percent/Status columns

**What we fixed**

- Fix Dockerfile build paths and runtime port
- Fix five flow defects found reviewing schema against navigation

**More changes**

- Initial commit: prototype with Dockerfile, compose, .env and CI workflow
- Test push for auto‑deployment

---

_Generated from git history. Each line is one change; the wording is the change's own, only grouped and simplified._
