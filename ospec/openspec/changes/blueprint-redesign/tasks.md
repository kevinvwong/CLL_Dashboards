# Tasks

## 1. Visual system

- [x] 1.1 Rewrite the token block: dark GT-navy chrome tokens, light content tokens, GT gold accent, `--ink-print`, and the six-value priority colour scale. *Verify: every token is declared once; the token test asserts no colour literal outside a token block.*
- [x] 1.2 Add the serif heading face and keep the sans body; apply `eyebrow → serif heading → note` to section headings. *Verify: a heading and its body differ in face; a section on any page renders the three-part heading.*
- [x] 1.3 Extend `app/status.py` with the priority colour scale; do not add a second status vocabulary. *Verify: a test asserts `status.vocabulary()` still equals the schema's CHECK; the priority scale has six distinct colours.*
- [x] 1.4 Rebuild the component set on the tokens: stage, panel, card, chip, stat tile, pill, table, drawer, dialog, empty state, breadcrumb, toast. *Verify: each component renders; buttons have variants; the progress bar exposes `role="progressbar"` with `aria-valuenow` and its number as text.*
- [x] 1.5 **Group check:** the token and component system carries the Outcomes page end to end with no regression. *Verify: `/oct16` renders on the new components; the design-system tests pass; a visual check at 375/726/1280px shows no horizontal scroll.*

## 2. Blueprint home

- [x] 2.1 Build the hero stage: a Dean node fanning into six colour-keyed priority cards, with the priority scale applied. *Verify: the home renders the node and six cards; each card carries a distinct priority colour, its code, name, and count.*
- [x] 2.2 Add the selected-priority panel: selecting a card shows that priority's definition and linked initiatives, with no page reload. *Verify: selecting a card updates the panel; it shows the priority's name, description, and initiatives.*
- [x] 2.3 Add the initiative-signals strip with per-initiative progress and an explicit no-update state. *Verify: each signal shows name and progress; an initiative with no update reads as no-update, not zero; no aggregate figure appears.*
- [x] 2.4 Rewire `/` to serve the stage from the reads the screen needs. *Verify: the home renders from named reads, not ad-hoc queries; the suite is green.*
- [x] 2.5 **Group check:** the home reads as an executive blueprint, not a tile grid. *Verify: the stage is the heaviest block; selecting each of the six cards works; a screenshot at 375/726/1280px shows the hierarchy.*

## 3. Cascade drill-downs and indexes

- [x] 3.1 Rebuild the goal and priority detail as a cascade: header, rollup label as total-plus-breakdown, initiative list grouped. *Verify: the header reads "N initiatives · M on track"; grouping by owner puts each header before its rows; no orphan header renders.*
- [x] 3.2 Show relationships on an initiative in the drill-down, both directions, with status and progress. *Verify: a D-1 that supports two Dean initiatives shows both, each with code, name, status, and progress.*
- [x] 3.3 Make each initiative row a single click target carrying code, name, owner, primary marker, progress, status, and age. *Verify: clicking anywhere on a row opens the detail; the progress bar exposes its value and its number as text.*
- [x] 3.4 Rebuild the `/initiatives` and `/people` indexes on the table component, filters in the query string. *Verify: a filtered URL lists only matching rows and the controls reflect the filter; an empty result shows an empty state offering to clear.*
- [x] 3.5 **Group check:** the cascade reads from outcome to work in one step. *Verify: from the home, reach a priority, then an initiative, then a person in clicks only.*

## 4. Initiative detail drawer

- [ ] 4.1 Move detail into a right-side drawer that opens over the list and updates the URL; a direct load renders the full page with no close control. *Verify: opening from a list opens the drawer and sets the URL; a direct load is a full page; Esc closes and returns focus to the opener.*
- [ ] 4.2 Apply the partial-response rule to every detail and edit endpoint. *Verify: a partial request carries no document element and no nav; a direct request carries both.*
- [ ] 4.3 Build the drawer layout: header with status, progress, owner and actions; facts; latest-update callout; relationships; diary newest-first. *Verify: the diary marks status changes; the relationships block shows status and progress.*
- [ ] 4.4 Build the in-drawer update form: progress control plus number input, status control limited to the schema's values, previous value shown, note with character count. *Verify: opening it on an initiative with a previous update shows that value and sets the controls; the status options equal the schema's values.*
- [ ] 4.5 Inline save into the drawer with a toast; a refused save keeps the input and explains inline. *Verify: a save updates the diary and the row and shows a toast without reloading; a refused save keeps the values.*
- [ ] 4.6 **Group check:** the update loop works without leaving the page. *Verify: open a list, open the drawer, save an update, see the row and diary change, close back to the same scroll position.*

## 5. Navigation, coverage, meeting and outcomes

- [ ] 5.1 Build the hybrid navigation, active state, `aria-current`, and the narrow-viewport collapse. *Verify: the active section is marked; at a narrow width the nav collapses behind a control.*
- [ ] 5.2 Add the stable `/outcomes` route with a permanent redirect from `/oct16`; add breadcrumbs below the top level. *Verify: the old route redirects permanently; an initiative detail shows its breadcrumb trail with linked ancestors.*
- [ ] 5.3 Add the user menu holding switch-user; keep meeting and outcomes first-class. *Verify: switch-user is in the menu and not in the nav; the meeting and outcomes are each one step from any page.*
- [ ] 5.4 Merge coverage into the admin page as a second section, distinct from checks. *Verify: both sections render with their own headings; coverage reports counts and completeness only, checks report pass/fail with records.*
- [ ] 5.5 Restyle `/meeting` on the new system and confirm print. *Verify: the meeting page renders on the components; printing contains the date range and all sections, with no nav, buttons, or banner.*
- [ ] 5.6 Restyle `/oct16` (now `/outcomes`) on the new system. *Verify: the outcomes page renders on the components with no visual regression to its content.*
- [ ] 5.7 **Group check:** every destination in the nav is reachable and correct. *Verify: walk each nav destination and the outcomes redirect.*

## 6. Verification

- [ ] 6.1 Visual check of every page at 375, 726, and 1280px, light content and dark chrome. *Verify: no page scrolls horizontally; the chrome and content palettes both render.*
- [ ] 6.2 Keyboard-only pass: nav, filters, the drawer, and the update form. *Verify: every interactive element is reachable and operable by keyboard, with visible focus and correct focus return.*
- [ ] 6.3 Print check on the meeting and the outcomes pages. *Verify: the printed output has no chrome and no interactive controls, and the content is complete.*
- [ ] 6.4 Run the whole suite and both validations. *Verify: the suite passes and `openspec validate --all --strict` exits 0.*
- [ ] 6.5 **Group check:** the redesign is complete and the superseded change is recorded. *Verify: `overhaul-ui-ux-navigation` is closed with its work carried into this change, and every item in groups 1–5 is checked.*
