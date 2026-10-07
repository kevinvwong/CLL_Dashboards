# Prompt for Claude in Chrome — second pass (post-fix) on the CLL Initiative Dashboard

Copy everything below the line into Claude in Chrome. It is self-contained. This
is a SECOND pass: a first review found ~27 issues, they have now been fixed, and
this pass checks the fixes and looks for anything new. Screenshots are requested —
see "Screenshots" below.

---

You are reviewing a locally-served web dashboard in a real browser. Produce a
structured markdown report. This is a **second pass**: the dashboard was reviewed
before, ~27 findings were fixed, and your job is three things —

1. **Verify the specific fixes** (listed below), saying for each whether it now
   behaves correctly.
2. **Look for anything new or regressed** the fixes introduced.
3. **Give an honest overall read**, same as a first-time reviewer would.

Be concrete: name the page, the element, what you saw. Measure where you can
(contrast, sizes, counts). Do not just summarise — critique, and rank by impact.

## Getting in

1. Go to **http://127.0.0.1:8000/** — a login page.
2. Passcode: **devpass**, submit.
3. "Who are you?" — pick **Bill** (the Dean). For one check you will also need
   **Kevin** (the admin) to see the admin controls; switch via the user menu
   (top-right) → "Switch user".
4. Navigate with the top nav and ⌘K / Ctrl-K search.

The data is **invented sample data** (the yellow banner says so). Judge the design
and behaviour, not the truth of the figures.

## Screenshots — please capture these

Use your screenshot/browser tooling to capture full-page shots. Name each file
clearly (e.g. `overview.png`). Capture at least:

1. `/` — the Overview, full page.
2. The **app bar** close up (crop to the top ~64px), so the GT logo, gold rule and
   nav are legible.
3. `/outcomes` — the Dean's outcomes page, full page (the six cards, and the
   "build memo" reveal collapsed).
4. `/outcomes` with the **memo reveal opened**, so the scope / data-requirements /
   trade-offs are visible.
5. `/major-initiatives` — the index table, full page.
6. `/major-initiatives/MI-021` — one Major Initiative detail page.
7. The **initiative drawer**: from `/initiatives`, click a row so the drawer opens,
   and capture it.
8. `/priorities/Identity` — a priority detail page.
9. `/checks` — the coverage/checks page.
10. The **search palette** with results showing (Ctrl-K, type "faculty").

If you cannot capture a screenshot, say which and why, and describe what you saw
instead. If your tooling can only do the viewport, say so — the first pass used an
894 × 601 viewport and several findings were viewport artefacts.

## The fixes to verify

For each, say **PASS**, **FAIL**, or **PARTIAL**, with the evidence.

1. **Shifted targets (data).** MI-021 `Develop approval/governance process…` must
   carry a target about *approval*, MI-022 `Establish and Implement Faculty
   Governance Process` a target about *governance*, MI-023 a target about
   *evaluation*, and so on through MI-028. Before the fix MI-021 showed MI-022's
   subject. Check MI-021…MI-029 on `/major-initiatives` or their detail pages, and
   say which (if any) still look mismatched.
2. **Search (Ctrl-K).** Enter should land on a styled page (or go straight to a
   single match), not a raw fragment. Typing `MI-001` must find that Major
   Initiative. Arrow keys should move a highlight; Enter should follow it.
3. **The `&minus;` bug.** On `/outcomes`, the two minus rows under Trade-offs
   should show a minus sign, not the literal text `&minus;`.
4. **Outcomes for the Dean.** The six cards should no longer show a bare
   `Owner: [no owner named] · updated [date]`. The owner line should read as a
   state. The internal planning memo (scope table, data-requirements, trade-offs)
   should be **collapsed** behind a reveal, so the default page is the six cards.
5. **Milestone counts.** Each card's "N of M milestones reached" must match the
   number of milestone rows shown beneath it (they were 1-of-4 over three rows).
6. **Wayfinding.** Breadcrumbs should sit inside the page gutter, not at the window
   edge. On MI pages the parent should be **Major Initiatives**, not Priorities.
   `/teams` should load (it used to 404). The current-page nav item should be
   highlighted correctly.
7. **Drawer controls.** The drawer's **Update** button (and the admin buttons as
   Kevin) should look designed, not the browser default. The **Feeds** line should
   be spaced rows with status badges, not one run-together string.
8. **Accessibility / legibility.** The logo should have a text alternative
   ("Georgia Tech"). Priority code text should pass contrast. Progress bar tracks
   should be visible. Badges and IDs should not wrap mid-word.
9. **One priority label.** A priority should read the same everywhere —
   e.g. `P01 One Shared Identity` on its own page, and `P01`+title in tables.
   Check `/priorities/Identity`, `/`, `/major-initiatives/MI-001`.
10. **Overview health.** The Overview should open with a one-line health read
    ("N initiatives tracked: X on track / Y at risk …") before the taxonomy.
11. **The goal eyebrow.** `/goals/1` should read "Goal G1", not "Goal ·".

## Also check

- **Coverage on `/checks`**: it should read as covered / not covered, not as
  full-width bars that look like quantities.
- **The health read** and any new element the fixes added — does it look right, fit
  the brand, and not clash?
- **Anything the fixes broke**: overlapping elements, spacing, a control that no
  longer works, a page that lost information.
- **The brand read**: with the logo covered, does it still look like Georgia Tech
  (navy bar, gold rule, gold eyebrows, cream bands, Barlow headings)? Does it look
  like 2026?

## How to report

One markdown document:

1. **Summary** — 3-4 sentences: overall verdict, and the single biggest remaining
   issue. State clearly whether the fixes landed.
2. **Fix verification** — a table: finding, PASS/FAIL/PARTIAL, evidence.
3. **New findings** — anything new or regressed, ranked by impact, each marked
   Critical / High / Medium / Low.
4. **Screenshots** — list the files you captured, and note any you could not.
5. **Top three remaining fixes**, in order.

Be concrete and quoted. If something is a matter of taste rather than a defect, say
so. **Read-only** — do not submit any form that writes data, and do not log out.
