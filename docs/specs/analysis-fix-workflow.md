# Workflow — resolve the browser-analysis findings

Source: `cll-dashboard-analysis-2026-10-06.md` (Claude in Chrome, 894×601 viewport).
Every finding is verified against the code before it is acted on, per the
session's habit: the previous review was about a third wrong on causes.

Legend: **[done]** landed · **[done]** to do · **[decided]** a judgment call made
here, with the reasoning, where the finding needed a product/vocabulary decision.

## Batch 1 — data integrity and Critical (committed)

- **#5 shifted targets [done]** The canon reorders source area "Academic Affairs";
  the seed joined titles to targets by position. Now joined by name, with the five
  renames mapped explicitly and a build that fails on an unmatched row. Regression
  test added.
- **#1 search Enter → raw page [done]** Direct load now renders `search.html`; a
  single match 307-redirects to it. htmx still gets the fragment.
- **#9 search misses Team Initiatives, no arrow keys [done]** Added a
  `team-initiative` kind (by MI-id and title); palette highlight + Enter.
- **#3 literal `&minus;` [done]** Entity moved outside the Jinja expression.
- **#21 `Goal ·` eyebrow [done]** Shows the goal number; drops the empty separator.
- **#13 priority-code contrast [done]** Code text is ink; hue stays on dot + border.
- **#14 progress track contrast [done]** `--line-track` (3.02:1 / 4.8:1).
- **#16 badges/IDs wrap mid-word [done]** `white-space: nowrap`.

## Batch 2 — wayfinding (#10, #26) [done]

- Breadcrumb at `x = 0`: put it inside `main`'s gutter.
- MI-001 breadcrumb says "Overview › Priorities › MI-001": wrong parent. The MI
  page's parent is the Team Initiatives index, not Priorities.
- Team breadcrumb links "Teams", which 404s. Point crumbs at real routes.
- `aria-current` marks the wrong nav item on goal/priority/team/MI pages (they
  highlight "Initiatives"); `/checks` highlights "Overview".
- Only some pages have breadcrumbs.
- `#26` `/checks` reports "all passing" while Outcomes shows placeholders: widen
  the checks, or say what it does not cover.

## Batch 3 — drawer, accessibility, progress (#11, #18, #15) [done]

- `#11` the drawer's Update control is the raw browser default; the Feeds line
  runs together with loose gold text instead of badges.
- `#18` the GT logo is a CSS background: add an accessible name.
- `#15` progress drawn three ways: bare %, varying-width bars, always-full `/checks`
  bars. Make one bar component and use it.

## Batch 4 — Outcomes (#2, #4, #12) [decided]

The `[no owner named] · updated [date]` line and the planning memo are **deliberate**
(documented in `LAUNCH_RECORD.md`). Decision: keep the *facts* but stop them reading
as broken on the Dean's view.
- `#2` reword the pending owner line so it reads as a state, not an unfilled variable.
- `#4` move "Scope and scale", the data-requirements table and the trade-offs behind
  a `?detail=1` reveal or to `/checks`, so the default Outcomes view is the six cards.
- `#12` list every milestone the count refers to, so the number reconciles.

## Batch 5 — vocabulary, naming, overview, colour, type (#6, #7, #8, #17, #19) [decided]

- `#7` **one label everywhere.** A priority shows `P01 One Shared Identity` on its
  own page, in tables and in search. The canon workbook carries short names only
  (`Identity`) and a *different* ordering (P3=Identity); the app's codes come from
  the prototype's `PRIORITIES` array and the DB keys on them, so this is a
  display-consistency fix, not a renumber. Recorded.
- `#6` **one status set.** Milestones keep the wireframe's five (`Met`, `In progress`,
  `Not started`, `Due Dec`, `Confirm`) — they are the October 16 data. Add a small
  legend so they are read as a set distinct from initiative status. Define `source`
  as a target status in words.
- `#8` add a one-line portfolio health summary above the taxonomy on the Overview.
- `#17` keep the codes; the warm hues already read near the At-risk amber, so add a
  legend or drop the dot on the Overview cards (the code carries the identity).
- `#19` pick one family for card titles (IBM Plex Sans, the UI face) so only ledes
  stay serif.

## Batch 6 — polish (#22, #23, #24, #25, #27) [done]

- `#22` US spelling ("organized").
- `#23` show "Ctrl K" as well as ⌘K.
- `#24` filters: apply on change where practical; fix the checkbox/label order.
- `#25` drop the repeated owner/team name under a group header; label the group.
- `#27` the user menu shows a name and role.

## Verification

After each batch: run `pytest` (509 at last count); rebuild the db and confirm it
still reproduces byte-for-byte; re-read the exact page in the browser where the
finding was visual.

## Result

All batches landed. Each item was verified against the code before it was acted
on; two claims in the analysis were found to be the reviewer's probe error rather
than defects, and several tests pinned old behaviour and were corrected with the
code they tested. The suite went 505 -> 510; the db rebuilds deterministically.

Commits: 2b59feb (#5 data bug), 9c4f114... the search/entity/contrast batch,
the wayfinding batch, 3b0482d (outcomes), 111d891 (drawer/a11y/progress),
3b5bdaf (vocabulary/label/health/type), and this polish batch.
