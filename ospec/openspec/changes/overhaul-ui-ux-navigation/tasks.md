# Tasks

> **SUPERSEDED 2026-10-06 by lueprint-redesign.** This change is closed, not deleted. Its 8 completed group-1 bug fixes are carried into the superseding change (tasks 1.x and 4.x), and its six spec deltas are rewritten there under the new navigation. See docs/superpowers/specs/2026-10-06-blueprint-redesign-design.md and openspec/changes/blueprint-redesign/proposal.md.

The remaining groups below were never implemented and are retained only as a record of what was planned.

## 1. Bug fixes

Ship these first: they are verified defects, independent of the design system.

- [x] 1.1 `edit_details.html` returns only the form fragment for partial requests and the full layout otherwise. *Verify: an HTMX request to `/initiatives/{code}/edit/details` returns no `<html>` and no site nav; a direct load still renders the full page.*
- [x] 1.2 The standalone initiative page omits the modal close control. *Verify: `GET /initiatives/{code}` contains no `data-close` / `×`; the fragment still does.*
- [x] 1.3 Goal and priority pages render each side only when it has rows, so no empty `<ul class="dean-rows">` and no orphan "D-1" divider appear. *Verify: rendering `list.html` with `dean_rows=[]` omits both the Dean `<ul>` and the divider; with `d1_groups=[]` omits the divider and group chrome.*
  - **Retargeted on import.** The recorded symptom was "group headers render in the wrong order". That does not reproduce: the emitted order is already `divider → label → its list` on all 11 goal and priority pages, and no CSS `order` is involved. The real defect is the unconditional chrome, which is invisible today only because every seeded goal and priority has both a Dean row and a D-1 group.
- [x] 1.4 Replace "On track 10" rollups with the total count plus a per-status breakdown. *Verify: the Academic goal header reads "10 initiatives · 10 on track", not "On track 10".*
- [x] 1.5 Pluralize day counts correctly. *Verify: a 1-day-old update reads "1 day since update"; a 15-day-old reads "15 days since update".*
- [x] 1.6 Add GET handlers for `/initiatives` and `/people`, and a styled 404 for unknown routes. *Verify: `/initiatives` and `/people` return 200 HTML, not a 405/404 JSON body; an unknown route returns a styled 404 with a link to Overview.*
- [x] 1.7 Give the goal and priority card links accessible names. *Verify: each card link has an accessible name containing the goal or priority name and its count.*
- [x] 1.8 **Group check:** every defect in this group is fixed and no route regressed. *Verify: the four named defects reproduce before the fix and not after; `/`, `/goals/{n}`, `/priorities/{name}`, `/initiatives/{code}`, `/meeting`, `/checks` all return 200.*

## 2. Design system foundation

Must land before any page migrates. Nothing here may introduce a status value the schema cannot store.

- [ ] 2.1 Extract CSS tokens (colour, spacing on a 4px scale, radius, shadow, type scale) from the Outcomes page, with dark-mode overrides. *Verify: two different pages render a card using the same radius/padding/border/shadow tokens; a grep finds no new literal colour outside the token block.*
- [ ] 2.2 Build the shared components: status pill, progress bar, initiative row, stat tile, card, chip, button variants, form field, drawer, modal, toast, empty state, breadcrumb. *Verify: each component renders in isolation; buttons use a defined variant; the progress bar exposes `role="progressbar"` with `aria-valuenow` and its number as text.*
- [ ] 2.3 **Status scale reads the schema, not the design.** The component's status classes and colours cover exactly the schema's `Status` CHECK values (`Not started`, `On track`, `At risk`, `Off track`, `Complete`, `Paused`). *Verify: a test asserts the component's status set equals the values parsed from `db/schema.sql`, and every emitted class has a CSS rule — the same check `status-presentation` uses.*
- [ ] 2.4 Replace the two-layer sample-data banner with one thin (≤32px) dismissible bar, leaving a "Sample data" marker in the footer. *Verify: after dismissing, the bar stays hidden on later pages for the session and the footer marker remains.*
- [ ] 2.5 Define the responsive breakpoints (≤640, 641–1024, >1024) and the collapsing nav. *Verify: at 375, 726, and 1280px no page scrolls horizontally; the nav collapses to a menu button at ≤640px.*
- [ ] 2.6 Add focus-ring styles, drawer and modal focus trapping, Esc to close, and focus return. *Verify: opening a drawer moves focus into it, Tab cycles within it, Esc closes it and returns focus to the row that opened it.*
- [ ] 2.7 **Group check:** the design system carries a page end to end before other pages migrate. *Verify: one page — the Outcomes page — is migrated onto the tokens and components with no visual regression, in light and dark modes.*

## 3. Navigation

- [ ] 3.1 New primary nav (Overview, Initiatives, People, Meeting, Outcomes) with an active state and `aria-current="page"`. *Verify: on any `/initiatives` page the Initiatives item is marked active and carries `aria-current="page"`.*
- [ ] 3.2 Add `/outcomes` and a 301 redirect from `/oct16`. *Verify: `GET /oct16` returns 301 with `Location: /outcomes`; `GET /outcomes` returns the page.*
- [ ] 3.3 Add a user menu containing the current user and Switch user. *Verify: Switch user is reachable from the menu and not present in the primary nav; the picker marks the current user.*
- [ ] 3.4 Move Data checks to an admin-only entry showing the count of failing checks. *Verify: with 2 checks failing the entry shows "2"; with none it shows no badge; a non-admin does not see the entry.*
- [ ] 3.5 Global search (⌘K / Ctrl+K) across initiatives, people, goals, and priorities. *Verify: ⌘K then "MAR-3" lists MAR-3 first and Enter opens its detail; Esc closes and returns focus.*
- [ ] 3.6 Breadcrumbs on every page below the top level. *Verify: an initiative full page reads "Overview › Initiatives › D-B" with each ancestor a link.*
- [ ] 3.7 **Group check:** every entity is reachable from the nav and from search, and no route is tied to a date. *Verify: navigate to each of the 5 nav destinations and to one initiative, person, goal, and priority by search alone.*

## 4. Portfolio views

- [ ] 4.1 Overview: portfolio health strip, status-breakdown bars on the goal and priority cards, and descriptions on the priority cards. *Verify: the strip reads Total, each status count, stale count, and the last meeting date; each tile links to the Initiatives index with that filter applied.*
- [ ] 4.2 Initiatives index: filterable and sortable table with filters in the query string. *Verify: `/initiatives?status=at-risk&owner=tim` lists only Tim's at-risk initiatives and the controls reflect those values; a no-match filter shows an empty state offering to clear.*
- [ ] 4.3 People index and person page: status breakdown, stale-update flag, sorted by attention. *Verify: `/people` lists every person with role, count, and breakdown; a person page orders off track, then at risk, then stale, then the rest.*
- [ ] 4.4 Goal and priority pages: header pattern, a group-by toggle (owner, tier, status), and each row as a single click target. *Verify: grouping by owner puts each owner's name directly above that owner's rows, Bill's group included; clicking anywhere on a row opens the detail.*
- [ ] 4.5 **Group check:** the portfolio screens answer "how is the portfolio, and who owns what" without opening an initiative. *Verify: from Overview, reach a filtered Initiatives list, a person page, and a grouped goal page in clicks only.*

## 5. Initiative detail and editing

- [ ] 5.1 Initiative detail in a right-side drawer that updates the URL to `/initiatives/{id}`; loading the URL directly renders the full page. *Verify: opening D-B from the Academic page opens the drawer, sets the URL, and leaves the list visible; Esc restores `/goals/1` and the scroll position; a direct load renders the full page with breadcrumbs and no close control.*
- [ ] 5.2 Detail layout: header (status, progress, owner, actions), facts block, Latest update callout, diary timeline newest-first marking status changes, and fed-by / feeds lists with status and progress. *Verify: a Fed-by row for an off-track 15% initiative shows a red "Off track" pill and 15%.*
- [ ] 5.3 Update form: labels above fields, segmented status control, slider paired with a number input (0–100), the previous value, a note field with a live counter (max 500), primary Save and secondary Cancel. *Verify: opening Update on a 45% On track initiative shows "Previous: 45% · On track" with controls set to those values; at 500 characters the counter reads "500/500" and input stops.*
- [ ] 5.4 Inline save: the row and detail update in place and a toast confirms, with no full reload. *Verify: saving 50% On track shows the "Update saved" toast, the list row shows 50% On track, and the diary gains an entry at the top; a rejected save keeps the form open with the entered values and an inline error.*
- [ ] 5.5 Edit details covers owner, goals and priorities (with the primary flag), tier, and the parent D-1 link, gated by role; fields the user may not edit are disabled with an explanation. *Verify: a user not permitted to change ownership sees the owner field disabled with "Only the Dean or an admin can change the owner".*
- [ ] 5.6 **Group check:** the update loop works end to end without a page reload. *Verify: open a list, open a drawer, post an update, see the row and diary change, and close the drawer back to the same scroll position — all without a full page load.*

## 6. Meeting review

- [ ] 6.1 "Since" defaults to the last meeting date, falling back to 7 days ago, with quick ranges (Last meeting, 7d, 14d) and a custom date. *Verify: with the last meeting on 2026-09-29, opening Meeting shows changes since 2026-09-29 with "Last meeting" selected.*
- [ ] 6.2 Agenda sections in order: Needs attention (cards with the latest note), Changes since (grouped by owner, collapsible), No update since (grouped by owner). *Verify: an at-risk initiative's card shows its note without opening the detail; an initiative with no update in range appears under "No update since".*
- [ ] 6.3 Show the progress and status change between updates. *Verify: an initiative moving from 20% At risk to 30% On track shows "20% → 30%" and "At risk → On track".*
- [ ] 6.4 Presenter mode: large type, one owner group at a time, arrow keys to move, Esc to exit. *Verify: the right arrow advances to the next owner's group and the position indicator updates (e.g. "2 of 5"); Esc exits.*
- [ ] 6.5 Print stylesheet and print view: no nav or interactive controls, every section expanded, the date range in the header. *Verify: printing contains the date-range header and all three sections expanded, with no nav, buttons, or banner.*
- [ ] 6.6 **Group check:** a real meeting can be run from the page. *Verify: with the sample data, the three sections populate, presenter mode steps through owners, and a print preview is clean.*

## 7. Admin checks

- [ ] 7.1 List every check rule with its name, a one-line description, and a pass/fail marker — not a single summary sentence. *Verify: with all rules passing, each is listed with a green "Pass", including "Every active D-1 initiative has a Dean link" and "Every initiative is tagged".*
- [ ] 7.2 Each failure lists the failing records and links to the fix. *Verify: with MAR-4 untagged, the "Every initiative is tagged" rule shows "Fail · 1" and lists MAR-4 with a link that opens its Edit details.*
- [ ] 7.3 **Group check:** the checks page is reachable only from the admin entry and drives a fix. *Verify: a non-admin does not see the entry; an admin follows a failing record to its fix and the rule then passes.*

## 8. Verification

- [ ] 8.1 Visual check of every page at 375, 726, and 1280px, in light and dark modes. *Verify: no page scrolls horizontally; every status colour meets WCAG AA in both modes.*
- [ ] 8.2 Keyboard-only pass: nav, search, drawer, update form, presenter mode. *Verify: every interactive element is reachable and operable by keyboard, with visible focus.*
- [ ] 8.3 Contrast check (WCAG AA) on all text and status pills. *Verify: measured contrast ratios meet 4.5:1 for body text and 3:1 for large text and UI components.*
- [ ] 8.4 Regression: saving updates, editing details, switching users, and the `/oct16` redirect all work. *Verify: the existing suite passes, plus the four named flows.*
- [ ] 8.5 **Group check:** the whole verification pass is green and the suite is green. *Verify: `python -m pytest tests -q` passes and every item in groups 1–7 is checked.*
