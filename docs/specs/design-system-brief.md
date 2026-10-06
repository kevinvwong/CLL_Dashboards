# Design-system brief — drop-in replacement for the CLL Initiative Dashboard

**For:** Claude, building the design system in its own tooling.
**From:** the CLL Initiative Dashboard repo.
**Deliverable:** drop-in files that replace the current stylesheet with **no
change to markup**. This is a restyle, not a rewrite of the app.

Read this whole brief before starting. It states the exact visual direction, the
token vocabulary, and the machine-checked rules your output must satisfy. Nothing
here is a suggestion — the guard tests in section 7 will run against your output.

---

## The goal — read this first

> **A reimagining of the Georgia Tech brand: ultra modern, but a clear evolution
> with clear lineage.**

This one sentence governs every decision below. Unpack it, because the two halves
pull against each other and the tension is the point:

- **Ultra modern** is the *execution*: current spacing, a real type hierarchy,
  restrained elevation, a calm dense-data layout. It should feel like software
  made in 2026, not a university site from 2015.
- **Clear lineage** is the *substance*: it must still, unmistakably, be Georgia
  Tech. Someone who knows the Institute should look at a screen and recognise it
  **with no logo present**.

So the failure modes are equal and opposite. A **dated, generic university
dashboard** fails the first half. A **generic modern SaaS dashboard with GT
colours sprinkled on** fails the second — and it is the more tempting mistake,
because it is easy to reach for Polaris or Material wholesale. Do not. Borrow
their *craft* (token discipline, elevation logic, spacing) and none of their
*identity*.

**The GT cues that must survive and be legible** — these are the lineage, and they
should read at a glance without a wordmark:

- **White and gold lead; navy is the counterweight.** The Institute's own rule,
  and the single strongest GT signal. A GT screen should feel *warm and bright*,
  punctuated by navy — not navy-dominant.
- **Gold as a rule and a mark, not a wash.** Hairlines, active states, small
  emphases. The gold-gradient heritage is a material to reference, not a
  background to flood.
- **The slab heading voice.** Roboto Slab is GT's sanctioned digital display face;
  its slab terminals are a direct line to the Institute's print and signage
  heritage. It is what makes the type feel *Georgia Tech* rather than *any app*.
- **The technical-institute character.** GT is an engineering school: precise
  alignment, measured proportions, honest data presentation. The design should
  read as *engineered* — exact, unhurried, trustworthy.

**The test to hold yourself to:** open the style guide and ask *"could this be any
university, or any SaaS product?"* If yes, it has lost the lineage — go back and
let the GT cues lead. Then ask *"does this look current?"* If no, it has lost the
modernity. The brief is satisfied only when both answers hold at once.

---

## 1. What you are building

Four things, delivered as files:

| # | File | What it is |
|---|------|-----------|
| 1 | `style.css` | The whole design system. One file, tokens + every component rule. |
| 2 | `print.css` | The print overrides (strips chrome, keeps content). |
| 3 | `fonts/` | Self-hosted woff2 font files + an `@font-face` block in `style.css`. |
| 4 | `style-guide.html` | A standalone page rendering every token and component, for review. Not linked from the app. |

### Where these files go (the integration contract)

The app is served by FastAPI with `app/static/` mounted at `/static`. Deliver the
files so they drop in **without touching the templates**:

```
app/static/style.css        # replaces the existing file (same path)
app/static/print.css        # replaces the existing file (same path)
app/static/fonts/*.woff2    # new folder, beside the two stylesheets
```

- **Paths inside the CSS are `/static/…`.** The page loads
  `<link rel="stylesheet" href="/static/style.css">`, so a font is referenced as
  `url("/static/fonts/roboto-regular.woff2")` — an **absolute URL beginning with
  `/static/`**, not `./fonts/…`. A relative path resolves against `/static/` and
  will 404 in some contexts; use the absolute form.
- **`style-guide.html` is a deliverable you hand back, not a file that ships.** It
  is for review. Keep it self-contained (inline the CSS, or link `/static/…`).
- Give me the files as a **zip or a directory tree**, plus a short note of what
  changed. I will copy them into `app/static/`, run the guard tests, and report.

The app is a FastAPI + Jinja2 dashboard, server-rendered, ~5,600 lines of HTML
across 33 templates that you will **not** be editing. Your CSS must style the
class names those templates already emit.

---

## 2. The visual direction (already decided — build this)

**Light-first, modern SaaS — executed with GT lineage.** Not dark chrome. The
craft of Polaris, Carbon-light and Fluent 2's light theme, carrying Georgia Tech's
identity (see "The goal" above). Concretely:

- **Chrome (header, nav, footer): white**, not dark. A strong bottom border or
  hairline in GT gold, not a filled navy bar. This is the clearest expression of
  "white and gold lead".
- **Content: near-white paper**, warmed slightly toward the GT Diploma tint
  rather than a cold grey. Cards are white with a subtle border and a soft low
  shadow. Surface hierarchy is expressed with **colour alternation and borders
  before shadows** (the Carbon approach), so dense tables stay calm.
- **Navy is the strong accent, not the dominant field.** Per the GT brand guide:
  "White and Gold should lead the visual palette... Navy can be used to add
  contrast and balance, without becoming the dominant color."
- **Elevation** is a small token set (Atlassian-style): a `sunken` level below the
  default surface (for table headers, code, inset areas), plus `raised` and
  `overlay`. Each has a matching shadow token.
- **Type: Roboto for all UI text, Roboto Slab for headings** (see §5). The slab is
  the lineage — let it carry the GT voice rather than reaching for ornament.
- **Generous, consistent spacing.** The app is projected in a leadership meeting
  and printed, so it must read at a distance and on paper. Prefer space and a
  clear type hierarchy over density tricks.
- **The instinct to avoid:** a generic modern dashboard wearing GT colours. Every
  surface should read as *engineered and warm* — precise, unhurried, clearly the
  Institute — not as a stock component library with a navy accent.

---

## 3. The colour system (official GT palette, 2026-27)

These are the real values from `brand.gatech.edu/our-look/colors`. Use them
exactly. Note the app's current navy `#003057` is **outdated** — do not use it.

### Core (the palette leaders)

| Token role | Name | Hex | Note |
|---|---|---|---|
| Gold | Gold | `#B39051` | Leads with white |
| Navy | Navy | `#051E39` | Contrast & balance, not dominant |
| Dark Gold | Dark Gold | `#8F713D` | **Use this for any gold *text*** |

### Secondary

| Name | Hex |
|---|---|
| Buzz | `#EAAA00` |
| Diploma | `#F9F6E5` |

### Accents (≤10% of a design, per the guide)

| Name | Hex |
|---|---|
| Campanile | `#048A81` |
| Whistle | `#660064` |
| Burdell | `#BBE6F2` |
| Azalea | `#D90368` |
| Tech Lawn | `#066034` |

### Brand rules you must honour

- **Gold text on white fails WCAG AA.** Use **Dark Gold `#8F713D`** for any gold
  text. (The guide says this explicitly.)
- Core-colour text must be **font-weight 500 or higher**.
- Accent colours are subordinate — they add interest, they do not lead.

### The six priority key colours (decided)

The app keys each of six priorities (P01–P06) to one colour so a reader can track
a priority across screens. **These are not status colours** and must never be
confusable with them. Use this GT-anchored set, tuned darker for legibility on
white and in print:

| Token | Hex | GT source |
|---|---|---|
| `--priority-1` | `#051E39` | Navy |
| `--priority-2` | `#8F713D` | Dark Gold |
| `--priority-3` | `#048A81` | Campanile |
| `--priority-4` | `#660064` | Whistle |
| `--priority-5` | `#004C97` | Bright Blue (gradient palette) |
| `--priority-6` | `#066034` | Tech Lawn |

> Note on `--priority-5`: the guide reserves Bright Blue `#004C97` for gradients.
> Using it here to reach six legible keys is a knowing, recorded deviation — keep
> it, and keep this note in a CSS comment.
>
> Note on `--priority-1`: it is the same navy as `--accent`, which is correct (the
> first priority is keyed to the Institute navy) but means a priority chip and an
> accent element share a colour. That is fine — the priority chip is a *key* shown
> beside a priority code, and the accent is chrome — but if it reads ambiguously in
> the style guide, prefer making `--priority-1` a touch lighter `#0A2A4D` and note
> the change.

### The status scale is NOT yours to choose

The six initiative statuses are read from the database schema and must keep their
current values. **Do not restyle them to brand colours** — a status colour is a
signal, not decoration, and changing it breaks a tested contract:

`On track #1b7f3b`, `At risk #b26a00`, `Off track #c0392b`,
`Not started #9a9a9a`, `Paused #9a9a9a`, `Complete #14532d`.
Their dark-mode values are in the current file; carry them forward (adjust only
if a contrast check demands it, and say so).

---

## 4. The output contract (read this twice)

The single most important constraint: **preserve every existing class name.**
The 33 templates emit them; renaming one silently breaks a screen.

- **Keep all class names exactly.** `.card-modal`, `.card-body`, `.badge`, `.bar`,
  `.bar-fill`, `.initiative-row`, `.tile`, `.button`, `.error-page`,
  `.breadcrumb`, `.toast`, `.drawer`, `.empty`, `.chip`, `.field`, `.button.primary`,
  `.button.secondary`, `.button.ghost`, `.status-*`, `.mi-*`, `.oct16-*`,
  `.goal-*`, `.team-*`, `.priority-*`, `.coverage-*`, `.delta-*`, `.presenter-*`,
  `.search-*`, `.user-menu`, `.nav-toggle`, and the rest — all of them.
- **You may add** new classes, tokens, and a style-guide page.
- **You may not** edit the templates, change an import, or rename anything the
  Python reads. The status class strings are generated in code
  (`status_class()` → `status-on-track`; `milestone_class()` → `m-in-progress`;
  `availability_class()` → `availability-*`). Those exact strings must have rules.
- **The app must run with zero template changes.** If a rule you want to write
  needs different markup, express it with a selector that already exists instead.

---

## 5. Typography

GT's digital-media typefaces are **free and self-hostable**:

- **Roboto** — all UI/text.
- **Roboto Slab** — headings and subheads.

Self-host as **woff2** in a `fonts/` folder. **No CDN link** — the app must work
with no external requests (it is served from Azure and often printed offline).

Required families and weights: Roboto 400 / 500 / 700; Roboto Slab 500 / 700.
Define them with `@font-face` and `font-display: swap`. Keep a system-font
fallback stack. **Do not use Georgia** — the current file does; the brand wants
Roboto Slab.

Keep a real type scale as tokens (the existing `--text-xs`…`--text-3xl` names must
survive — see §6). Every `font-size` in the sheet must be a `var(--text-*)`.

---

## 6. The token system

Every value is a custom property declared in `:root`, with dark-mode overrides in
a `@media (prefers-color-scheme: dark)` block. **No colour literal, and no bare
`font-size: Xrem`, may appear anywhere outside those blocks.**

### These token names must exist and be used (the guard tests check for them)

Spacing: `--space-1 --space-2 --space-3 --space-4 --space-5 --space-6 --space-8`
Radius: `--radius-sm --radius-md --radius-lg --radius-pill`
Type scale: `--text-xs --text-sm --text-base --text-lg --text-xl --text-2xl --text-3xl`
Shadow: `--shadow-sm --shadow-md` (you may add `--shadow-lg`, elevation tokens)
Families: `--font-sans` (Roboto), `--font-serif` (Roboto Slab)
Colour (keep these names; retune the values):
  `--ink --ink-muted --ink-subtle --surface --surface-sunken --surface-raised
   --surface-hover --line --line-strong --backdrop --accent --on-accent
   --error --warn-bg --warn-border --warn-ink
   --status-on-track --status-at-risk --status-off-track --status-not-started
   --status-paused --status-complete
   --priority-1 --priority-2 --priority-3 --priority-4 --priority-5 --priority-6`

Add elevation tokens (e.g. `--elevation-sunken`, `--elevation-raised`,
`--elevation-overlay`) and any neutral ramp you want — but keep the names above.

**Important:** the guard test greps token names for
`ink|surface|accent|line|error|warn|status|backdrop` and requires each to be
**both declared and referenced**, and **overridden in dark mode**. So if you
declare a new `--surface-*` or `--status-*` token, you must use it and give it a
dark value.

### Dark mode

The app already supports `prefers-color-scheme: dark`. Every colour token declared
in `:root` must also appear in the dark block. Missing one leaves that surface
light — a bug the tests catch.

---

## 7. The guard tests your output must pass

These run unchanged against your `style.css` and `print.css`. Each is a hard
pass/fail. Some assert **exact strings** — where a rule is quoted below, reproduce
that text verbatim (selectors, property value and spacing), because a regex or an
`in css` check looks for the literal characters. Reordering a multi-selector list
or changing `2px` to `0.125rem` will fail a test even though the rendered result is
identical.

### 7a. Token discipline (`test_design_system.py`)

1. **No colour literal outside a token block.** A `#hex` or `rgba(` anywhere except
   inside `:root` or the dark-mode block fails. Comments are stripped first, so you
   may name hex values in prose.
2. **Every colour token is both declared and referenced.** A token you declare but
   never `var()` fails; a `var()` you never declared fails. The check greps token
   names for `ink|surface|accent|line|error|warn|status|backdrop` — so a new
   `--surface-*` / `--status-*` token must also be used and dark-overridden.
3. **Required spacing / radius / type / shadow tokens exist** (the exact names in §6).
4. **Dark mode overrides every colour token** in `:root` whose name matches
   `ink|surface|accent|line|error|warn|status|backdrop`.
5. **No `font-size: X rem` literal** outside tokens.
6. **Component classes are defined** (each must appear as a rule): `.card-modal
   .card-body .badge .bar .bar-fill .initiative-row .tile .button .error-page
   .breadcrumb .toast .drawer .empty .chip .field`.
7. **Button variants exist:** `.button.primary`, `.button.secondary`,
   `.button.ghost`.
8. **Status classes cover exactly the schema statuses.** For each of the six
   statuses its class (`status-on-track`, `status-at-risk`, `status-off-track`,
   `status-not-started`, `status-paused`, `status-complete`) must have a rule.
   **Do not invent a status the schema cannot store** — a `status-done` class fails.

### 7b. Visual system (`test_visual_system.py`)

9. **Six priority tokens exist in `:root`:** `--priority-1` … `--priority-6`.
10. **They are all distinct values** (two priorities sharing a colour fails).
11. **Each is overridden in the dark block.**
12. **No priority colour equals a status colour** (the two scales must never be
    confusable — a shared hex fails).
13. **`h1 {` and `h2 {` rules use `var(--font-serif)`.** These are matched as
    `^h1 {`/`^h2 {` at line start — keep them as their own top-level rules.
14. **A `body {` rule uses `var(--font-sans)`.**
15. **`.eyebrow`, `.section-heading`, `.section-note`** each have a rule.
16. **No colour literal outside tokens** (same as 7a.1).

### 7c. Layout, focus and print behaviour (`test_design_system_behaviour.py`, `test_navigation.py`, `test_verification.py`)

17. **Three breakpoints, exact text:** `@media (max-width: 640px)`,
    `@media (min-width: 641px) and (max-width: 1024px)`,
    `@media (min-width: 1025px)`.
18. **No horizontal overflow guard:** the sheet contains the literal
    `overflow-x: hidden`.
19. **The no-JS nav collapse:** the sheet contains the literal selector
    `.nav-toggle:checked ~ .site-nav`.
20. **Focus ring:** the sheet contains `:focus-visible` **and** the exact string
    `outline: 2px solid var(--accent)`.
21. **Overlay scroll lock:** the sheet contains `overflow: hidden` (for
    `body.overlay-open`).
22. **The sample-data bar caps at 32px:** the `.sample-banner` rule must contain
    `max-height: var(--space-8)`.
23. **The banner is hidden for print:** a print rule hides `.sample-banner`
    (`@media print { … .sample-banner … }`).
24. **The nav is hidden for print, exact text:** `print.css` (or `style.css`) must
    contain the literal `.site-nav, .nav-toggle-label { display: none; }`.
25. **Print hides the presenter:** `@media print { … .presenter … display: none }`
    (or `.presenter { display: none; }`).
26. **A mid-width breakpoint exists:** `@media (max-width: 900px)` or
    `@media (max-width: 1024px)` (in addition to the 640px one).

### 7d. Status / milestone / availability colour rules (`test_status_presentation.py`)

27. **Every generated status class has a rule** (`status-*`).
28. **Every status has a badge colour rule:** `.badge.status-on-track`,
    **`.badge.status-at-risk`**, … for all six. (The old sheet scoped status colour
    to `.bar-fill.status-*` only, and the badge rendered uncoloured — this test
    exists because of that bug.)
29. **Every milestone class emitted by the data has a rule.** The exact set today
    is: `.m-confirm`, `.m-due-dec`, `.m-in-progress`, `.m-met`, `.m-not-started`.
    The test derives the set from `oct16_data.OUTCOMES`, so cover all five.
30. **Every availability class emitted by the data has a rule.** The exact set
    today is: `.availability-build`, `.availability-derived`,
    `.availability-have-it`, `.availability-no`, `.availability-partial`.

### 7e. Tokens referenced by literal name (`test_verification.py`)

31. The sheet contains the literal `--surface:` and `--accent:` declarations
    (so those two token names must be spelled exactly).
32. The dark block opener is the literal `prefers-color-scheme: dark`.

If you are unsure which classes exist, grep the templates in `app/templates/` and
the string data in `app/oct16_data.py` — every class emitted there must have a rule.
The guard tests are in `tests/`; read them before you finish.


---

## 8. What NOT to do

- **Do not change class names or touch templates.** (§4)
- **Do not invent statuses** or restyle the status scale to brand colours. (§3, §7)
- **Do not use a CDN font** or any external request.
- **Do not put a colour/rgb/font-size literal outside the token blocks.**
- **Do not use the old navy `#003057`** or the prototype's off-brand priority
  colours (`#53d7e8`, `#9a8cff`, `#ff7f6e`, `#42d39b`, `#ef8ad2`).
- **Do not use Georgia** as the heading face.
- **Do not remove** the print stylesheet's existing behaviour: it hides
  `.site-header`, `.site-nav`, `.nav-toggle-label`, `.sample-banner`,
  `.meeting-controls`, `.presenter`, `.no-print`, and keeps the content.

---

## 9. Acceptance checklist (self-check before you hand back)

- [ ] `style.css` + `print.css` + `fonts/` + `style-guide.html` delivered.
- [ ] Grep your `style.css`: no `#` hex or `rgba(` outside `:root` / dark block.
- [ ] Grep your `style.css`: no `font-size:` with a literal unit.
- [ ] All required token names from §6 present.
- [ ] Every colour token in `:root` also in the dark block.
- [ ] All 15 component classes from §7a.6 have rules; three button variants exist.
- [ ] All six `status-*` classes have rules; no invented status.
- [ ] Every `.badge.status-*`, `.m-*` and `.availability-*` class has a rule (§7d).
- [ ] The exact-string rules from §7c are present verbatim (breakpoints, focus
      outline, nav-collapse selector, `max-height: var(--space-8)`, print
      `.site-nav, .nav-toggle-label { display: none; }`).
- [ ] `h1`/`h2` use `var(--font-serif)`; `body` uses `var(--font-sans)` (as their
      own top-level rules).
- [ ] Fonts self-hosted at `/static/fonts/…`; no external URL anywhere in the CSS.
- [ ] Roboto + Roboto Slab used; Georgia gone; `#003057` gone.
- [ ] The six priority tokens use the hybrid set in §3, are distinct, dark-overridden,
      and share no value with a status colour.
- [ ] `style-guide.html` renders every token and component on one reviewable page.

**The goal check — do this last, and be honest:**

- [ ] Looking at the style guide, **could a GT person recognise it as Georgia
      Tech with no logo present?** (lineage)
- [ ] Does it **look like software made in 2026**, not a dated university site?
      (modernity)
- [ ] Is it **white-and-gold-led**, with navy as a counterweight rather than the
      dominant field?
- [ ] Does it read as **engineered and warm** — the Institute — and not as a
      stock component library with a navy accent?

When you hand back, note any place you **deviated** from this brief and why. A
recorded deviation is fine; an unrecorded one is a defect.
