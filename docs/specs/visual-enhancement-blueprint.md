# CLL Initiative Dashboard — Visual Enhancement Blueprint

> **Provenance:** supplied by the user 2026-10-07, as
> `CLL Dashboard Visual Blueprint (1).md`. A design input, not an approved
> change: it recommends, it does not commit. Nothing here is scheduled.
> Where it names a current behaviour, that claim was checked against the live
> app on receipt (see "Reconciliation with the current build" at the end).

Design Recommendations

This blueprint identifies the specific places in the dashboard where **data
visualization, color, and motion** would most improve legibility, executive
confidence, and contributor clarity — with before/after sketches for each.
Recommendations are organized by page location, from most visible to most
tactical.

High exec impact · Navigation / orientation · Accessibility improvement

---

## Overview → Header

### Stat Tiles — Add context and proportion

*Visualization*

**21 of 29 need review — show the ratio.** The "21 NEED REVIEW" tile is the most
alarming number on the page, but it sits next to "29" with no visual connection.
A thin fill bar under each tile encodes the proportion at a glance. The yellow
tile immediately reads as a problem; the others read as context.

```
29              6              21
Initiatives     Priorities     Need review
all teams       FY27 plan      72% of portfolio   <- fill bar at 72%
```

### Add semantic color to the "21" tile

*Color + Icon*

Right now the 21 renders in the same yellow as "NEED REVIEW" and the number
itself carries no background color or icon. Giving the tile a yellow border and a
⚠ icon makes it immediately legible without reading the label — useful in
projection and peripheral vision.

- **Now:** yellow text color only. Blends in on quick scan.
- **After:** yellow border + ⚠ icon + fill bar at 72%. Immediately signals action.

---

## Overview → Strategy 2035

### The Five Goals — Add icons and proportional weight

*Icon + Color*

**Each goal needs a distinct icon and hue.** G1–G5 chips appear throughout the
dashboard (strategy alignment, cascade view, initiative detail) but carry no
visual identity — they are colored dots that require reading. Assigning each goal
a unique icon and hue creates a system: users learn it once and recognize it
everywhere.

Proposed goal identity: Academic · Extension · Learner · Research · Operational.

### Show initiative distribution proportionally

*Data Visualization*

Academic (18), Research (12), Learner (11) vs Extension (7) and Operational (10) —
that distribution is invisible in the current flat pills. A small inline bar or
dot chart makes the strategic weight of each goal immediately readable.

---

## Overview → Annual Priorities

### Six Priority Cards — Add health and progress at a glance

*Color + Icon*

**The colored dots have no meaning — give them one.** Each priority card has a
colored dot (navy, purple, yellow, blue, orange, teal) but no legend and no
consistent meaning. These should either encode health status (on-track /
at-risk / not-started) or be removed. Using the Outcomes tab's "on track / at
risk" logic here connects the two views.

- **Now:** six dot colors, no legend, no semantic meaning.
- **After:** dot color = health status (green / yellow / gray), pulled from
  Outcomes data, with a legend once at section level.

### Add an initiative progress bar to each priority card

*Accessibility improvement · Data Visualization*

"5 initiatives · View cascade →" tells you the count but nothing about status.
A micro-bar showing Not started / In progress / Complete makes each card a status
summary, not just a label. Matching color to the health status ties it together.

```
Priority 1 · One Shared Identity
5 initiatives
● 1 complete  ● 1 in progress  ○ 3 not started
```

---

## Overview → Organizational Layer

### Four Team Cards — Color identity and comparative sizing

*Color + Identity*

**Assign each team a persistent color.** The four teams (Learning Ecosystems,
Learning Experiences, Learning Futures, Learning Infrastructure) appear
throughout the dashboard but are always text-only. A persistent team color used
consistently — on cards, in the initiatives table TEAM column, in the cascade
view — lets users track their team at a glance.

---

## Overview → Dean Initiatives

### Dean Initiatives — Visualize the FY timeline

*Data Visualization — highest executive visibility*

**"3 complete in FY26 · 8 in flight in FY27" is pure text — this is the Dean's
view.** This section sits directly above the footer and carries the most
senior-level summary on the page, yet renders as a single line of unstyled text.
This is the section the Dean will look at first. Even a simple timeline bar
encoding FY26 vs FY27 progress would raise the page's executive credibility.

---

## Outcomes Tab → Priority Cards

### Milestone Cards — Replace text counts with visual rings

*Data Visualization*

**"1 of 3 milestones reached" should be a ring, not a sentence.** The Outcomes tab
is the closest thing the dashboard has to a KPI view — but progress is expressed
as "N of 3 milestones reached" in plain text. A circular progress ring at the top
of each card communicates the same information in a fraction of a second, freeing
the text for the milestone detail below.

### Milestone status chips need icons, not just color

*Accessibility + Color*

MET, IN PROGRESS, NOT STARTED, DUE DEC, CONFIRM are all text-only right now.
Adding a small icon to each status chip makes the state readable in peripheral
vision and for users who cannot distinguish hue.

- **Now:** text chips with no color or icon; MET and NOT STARTED look identical.
- **After:** ✓ MET · ↻ IN PROGRESS · ○ NOT STARTED · ⚑ DUE DEC · ? CONFIRM —
  redundant icon + color encoding.

---

## Cascade View (Priority drill-down)

### Cascade — Show the hierarchy, not just the list

*Data Visualization — structural*

**The cascade view is a list; it should be a diagram.** The name "cascade"
implies a flow — Strategy → Priority → Initiatives → Owners — but the current
view renders as a flat list grouped by owner. A simple tree or swimlane diagram
showing which MIs feed a priority, and which owner owns each, would make the
cascade legible at a glance in a leadership meeting.

### Progress bars in the cascade list are imperceptible

*Visual*

Each initiative in the cascade list shows a thin gray bar as a progress
indicator, but all 29 initiatives are "Not started" so every bar reads
identically empty. When data arrives, these bars need to be thick enough (at
least 6px), labeled with a percentage, and colored by status to be readable.

- **Now:** ~2px gray hairlines, all identical, right-aligned in a narrow column.
- **After:** 6px bars, color-coded (gray=0%, blue=in progress, green=complete),
  with a % label.

---

## Global — All pages

### Navigation and global color system

*Navigation*

**Tab bar has no icons — add them.** Overview, Initiatives, People, Outcomes are
text-only with an underline active state. Adding a small icon to each makes them
scannable without reading and improves hit target on mobile.

**Consolidate to a single semantic color vocabulary.** The dashboard has two
color systems in parallel: the six arbitrary priority dot colors, and the
semantic on-track/at-risk green/yellow from the Outcomes tab. These need to
unify. The semantic health colors should win — they communicate status — and the
priority dots should either adopt them or use the goal color system.

Proposed unified semantic palette (traffic-light): on track · at risk · off
track · not started, plus GT Navy and GT Gold for brand.

---

## Global — Interaction design

### Motion — Where animation earns its place

| Move | Effect |
|---|---|
| **Progress bars fill on load** | All bars animate 0 → value on first render. One second, ease-out. Signals the data is live. |
| **Stat tiles count up** | The big numbers count up from 0 over ~0.6s. Draws the eye. Skip for `prefers-reduced-motion`. |
| **Milestone rings draw in** | SVG `stroke-dashoffset` animates to the fill position, 0.8s, staggered. |
| **Cascade diagram node reveal** | Nodes fade in left-to-right from the priority node, 40ms stagger. |
| **Card hover elevation** | Cards/rows lift 2px on hover. Signals they are interactive links, not labels. |
| **Filter/sort transitions** | Table rows animate their reorder rather than snapping; confirms the filter fired. |

**One rule for all motion:** every animation must respect
`prefers-reduced-motion: reduce`. Wrap animations in
`@media (prefers-reduced-motion: no-preference)` or suppress the keyframes when
the media query fires.

---

## Reconciliation with the current build (checked 2026-10-07)

A few of the blueprint's "now" descriptions are pre-fix; the record is corrected
here so the recommendations aren't planned against a state that no longer exists.

| Blueprint's "now" | Actual state |
|---|---|
| Dean Initiatives render as "a single line of unstyled text" | They are a full section on `/dean-initiatives` with percent bars and the 61 rolled-up initiative chips. The timeline-bar idea still applies. |
| Progress bars are "~2px gray hairlines … indistinguishable" | They are 0.6rem (~9.6px) bars; the *empty-track* bug (a `<span>` that could not take a width) was fixed 2026-10-07. Colour-coding and a % label remain unbuilt. |
| "21 NEED REVIEW tile … no visual connection" | The tile already links to a filtered view (`/team-initiatives?target=needs_review`). A fill bar / icon remains unbuilt. |
| Priority dots "have no legend" | Confirmed — 6 dot colours, no key, and the dots are `aria-hidden` (decorative). The health-encoding idea is open. |
| Tab bar text-only | Confirmed. |
| `prefers-reduced-motion` | A reduced-motion block already exists in `style.css`; any new motion must join it. |
