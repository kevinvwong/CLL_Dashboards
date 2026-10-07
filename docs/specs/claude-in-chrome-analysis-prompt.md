# Prompt for Claude in Chrome — analyse the CLL Initiative Dashboard

Copy everything below the line into Claude in Chrome. It is self-contained.

---

You are analysing a locally-served web dashboard with a real browser. Your job
is to produce a **full analysis** of it and report it back as structured markdown.
Do not just summarise the pages — critique them, rank the findings by impact, and
be specific (name the page, the element, what you saw).

## Getting in

1. Go to **http://127.0.0.1:8000/** — you will land on a login page.
2. Enter the passcode **devpass** and submit.
3. You will be asked "Who are you?" — pick **Bill** (the Dean). This matters: the
   app shows different things to different people, and Bill is the primary user.
4. You are now on the dashboard. Keep this tab; navigate with the top nav
   (Overview · Initiatives · People · Outcomes), and the ⌘K / Ctrl-K search.

The site is server-rendered and needs no special setup. If a page 404s, note it
(it may be intentionally disabled) and move on.

## What the app is

A strategy-portfolio dashboard for the Georgia Tech College of Lifetime Learning
(CLL), used by the Dean and his leadership team in a weekly meeting. It tracks
Major Initiatives, annual Priorities, Strategy 2035 goals, and outcomes. It was
just restyled onto a new design system called **Hive** (a Georgia Tech-derived
visual language: GT navy, gold, Diploma cream, Barlow + IBM Plex type, an official
GT logo in the top bar). All data on it is **invented sample data** — the yellow
banner says so. Judge the *design and usability*, not the truth of the figures.

## Pages to visit

Visit all of these and look at each properly (scroll, open panels):

- `/` — the Overview
- `/initiatives` — the Initiatives table (try its filters)
- `/goals/1` — a Strategy 2035 goal's cascade
- `/priorities/Identity` — a priority detail (Measure / Target / Cadence / Owner)
- `/teams/1` — a team page
- `/major-initiatives` — the 29 Major Initiatives index (try the filter and grouping)
- `/major-initiatives/MI-001` — one Major Initiative's detail page
- `/people` and `/people/2` — the People index and a person
- `/outcomes` — the October 16 outcomes view
- `/checks` — the data-checks page (admin; if you cannot see it as Bill, say so)

Click into an initiative row to open its detail drawer. Open the search (Ctrl-K).
Hover and focus things. Try a table filter.

## What to analyse — four lenses

Produce a section for each. In every section, name the specific page and element.

### 1. Visual design and brand

- Does it read as modern software (2026), and does it read as **Georgia Tech**
  specifically — navy bar with a gold rule, gold eyebrows, cream bands, Barlow
  headings, an official GT logo? Or could it be any university / any SaaS product?
- **The app bar**: is the GT logo visible, correctly sized, not distorted or
  overlapping? Is the gold rule under the bar present? Do the nav links read well
  against the navy?
- Typography: is the hierarchy clear (headings vs body vs labels)? Any font that
  failed to load (fallback looking wrong)? Any text that is too small or too large.
- Colour: does the palette feel coherent and warm (Georgia Tech gold/cream/navy)?
  Is anything garish, muddy, or clashing? Do the six priority colours read as a
  deliberate scale rather than random?
- Spacing, alignment, borders, radii: anything cramped, misaligned, or visibly off.

### 2. Usability and flow

- Can you tell, in the first five seconds on the Overview, **how the portfolio is
  doing**? Or is it organised around taxonomy rather than status?
- Is every clickable thing obviously clickable, and does it go where you expect?
- Are there dead ends — buttons, tiles, or links that do nothing, or 404?
- The KPI table's filter and "group by" controls: do they work and are they
  discoverable?
- The initiative drawer (open a row): does it open, read well, and close cleanly?
- Search (Ctrl-K): find something; is the result useful and the navigation correct?
- Anything where you had to *think* about what to do next — that is a finding.

### 3. Data presentation

- Are numbers and statuses encoded well? Are progress bars proportionate and
  legible (can you see the bar's full track and its fill)?
- Status colours: are On track / At risk / Off track / Not started / Paused /
  Complete distinguishable, and is the **word always present** with the colour?
- The priority key colours on cards: do they help or confuse?
- Tables: are columns aligned, headers clear, anything truncated or wrapped badly?
- Is there enough context (counts, denominators, comparisons) or are there bare
  numbers with no frame of reference?
- Any chart, bar, or figure that is misleading or hard to read.

### 4. Accessibility (WCAG 2.1 AA, best effort from the browser)

- Contrast: any text that looks too low-contrast, especially gold on light, status
  text on tinted badges, or muted grey helper text.
- Colour-only encoding: is any meaning carried by colour alone (no word, no icon)?
- Keyboard: Tab through a page — can you reach and operate the nav, the table
  filters, and the drawer? Is the focus ring visible on both the navy bar and the
  white content?
- The logo and icon-like elements: are they announced sensibly (do they have text
  alternatives), or purely decorative?
- Note: you may not be able to run a screen reader; describe what you can infer
  from the DOM and the tab order if your tooling exposes it.

## How to report

Return **one markdown document**, structured as:

1. **Summary** — three or four sentences: what this is, and your honest overall
   impression (strong / promising / mixed / weak), with the single biggest issue.
2. **What works well** — a short list, each with the page and why.
3. **Findings, ranked by impact** — a table or list. For each: a one-line title, the
   page, what you saw, and why it matters. Mark each **Critical / High / Medium /
   Low**. Put the things that would embarrass a presenter in front of the Dean at
   the top.
4. **Per-lens detail** — the four sections above, written out.
5. **The top five fixes** — if only five things were changed, which, in order.

Be concrete and quoted: "on `/major-initiatives`, the third column header reads X
and is clipped" beats "some tables have issues". If something looks broken, say
what you expected and what you saw instead. If you are unsure whether something is
a bug or intentional, say so rather than asserting.

Do not modify anything, do not fill in forms that write data, and do not log out.
Read-only analysis.
