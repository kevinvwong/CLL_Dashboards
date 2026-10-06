# Design-system brief — restyle the CLL Initiative Dashboard with Hive

**For:** opencode, working in this repo.
**From:** Kevin Wong (Strategic Operations, CLL), with the Hive design system.
**Deliverable:** a restyle of `app/static/style.css` and `app/static/print.css`,
self-hosted fonts in `app/static/fonts/`, and a review page — **with no change
to templates or Python**. This is a restyle, not a rewrite of the app.

**Source of truth: Hive.** Hive is the design system for this dashboard and the
decks and reports that come out of it. Where this brief and your instincts (or
the previous version of this brief) disagree, Hive wins. A copy of Hive ships
with this brief at `docs/specs/hive/` — read `README.md` there first, then
`dashboards.md` and `data-visualization.md`. Every colour, size and font below
is taken from Hive's `tokens.json`; do not invent values.

Read this whole brief before starting. Section 7 lists the guard tests; they run
against your output, and section 8 lists the two test edits this restyle requires.

---

## The goal

> **A reimagining of the Georgia Tech brand: ultra modern, but a clear evolution
> with clear lineage.**

- **Ultra modern** is the execution: a real type hierarchy, restrained
  elevation, small radii, calm dense-data layout. Software made in 2026.
- **Clear lineage** is the substance: someone who knows the Institute should
  recognise it with no logo present.

Hive resolves that tension with these cues. Keep every one legible:

1. **White and gold lead; navy steadies.** Pages are white. Gold is the primary
   action, the 3px rule and the eyebrow. Navy is the ink and the one solid bar
   across the top of the app.
2. **Gold as a rule and a mark, never a wash.** No gold backgrounds larger than a
   button; no gradients in product UI.
3. **The engineered display voice.** Headings are **Barlow** (open-source, the
   same signage-and-engineering lineage as GT's DIN 2014). Body and UI are **IBM
   Plex Sans** (GT's own named web alternate for Adelle Sans). Ledes and reading
   text may use **IBM Plex Serif** (GT's alternate for Adelle).
4. **The 30° facet.** GT's hexagon becomes one cut corner (`--chamfer-sm`, 8px)
   on the primary button only. One chamfered element per region.
5. **Honest data.** Status always carries its word (and in Hive, an icon);
   numbers right-aligned in tabular figures; one y-axis.

**The test:** open the review page and ask "could this be any university, or
any SaaS product?" If yes, the lineage is lost. Then ask "does this look
current?" If no, the modernity is lost. Both must hold.

---

## 1. What you are building

| # | Path | What it is |
|---|------|-----------|
| 1 | `app/static/style.css` | The restyled sheet: Hive tokens + every existing component rule. |
| 2 | `app/static/print.css` | Print overrides (keep current behaviour, apply Hive print rules). |
| 3 | `app/static/fonts/*.woff2` | Copy the ten files from `docs/specs/hive/fonts/`, plus their `LICENSE-*.txt`. |
| 4 | `docs/specs/hive/style-guide.html` | A standalone review page rendering every token and component class. Not linked from the app. |

**Approach: edit the current sheet, do not rewrite it.** The current
`style.css` already passes every guard test and styles every class the
templates emit. Change it in place:

1. Replace the `:root` and dark-mode token values with the Hive values in §3–§6.
2. Add the new tokens in §3 (`--gold`, `--action-primary`, `--chrome`, status
   backgrounds, `--font-display`, `--chamfer-sm`, …).
3. Restyle rules in place (chrome, buttons, badges, cards, tables) per §2 and §4.
4. Keep every selector. Do not delete a rule even if it looks unused (section 4
   lists classes that look unused but are emitted from Python).
5. Run `pytest` after each step.

Font URLs are absolute: `url("/static/fonts/barlow-600.woff2")`. No CDN, no
external request of any kind: the app runs on Azure and is printed offline.

---

## 2. The visual direction

- **App bar (`.site-header`): GT Navy** `--chrome`, white text, with a **3px GT
  Gold bottom rule**. `.brand` in Barlow 600, `--text-lg`. Nav links in IBM Plex
  Sans 500, white at rest; the current page (`.site-nav a[aria-current=page]`)
  gets a 3px gold underline and full-white text. On the bar, focus rings use
  `--focus-on-chrome` (Buzz), because Bright Blue disappears on navy.
- **Page:** `--surface` (white by day). Alternate bands and table headers use
  `--surface-sunken`, which is **GT Diploma** by day: this is where the warmth
  comes from. Cards are `--surface-raised` (white) with a 1px `--line` border and
  no shadow; shadows are for menus (`--shadow-md`) and dialogs (`--shadow-lg`).
- **Primary action:** `.button.primary` is GT Gold fill (`--action-primary`),
  navy ink (`--on-action-primary`), 1px `--gold-ink` border, `--radius-md`, and
  the chamfer:
  `clip-path: polygon(0 0, calc(100% - var(--chamfer-sm)) 0, 100% var(--chamfer-sm), 100% 100%, 0 100%);`
  One per view. **Never white text on gold.**
- **Secondary:** `.button.secondary` is Bright Blue fill (`--accent`) with
  `--on-accent` ink. **Ghost:** transparent, `--ink`, hover `--surface-hover`.
  Quiet/outline buttons (`.button` alone): transparent, 1px `--line-strong`.
- **Headings:** `h1`, `h2` in `var(--font-display)` (Barlow 600). `h3` and card
  titles in IBM Plex Sans 600. `.eyebrow`: Barlow 600, `--text-xs`, uppercase,
  letter-spacing 0.12em, `--gold-ink`, preceded by a 24×3px `--gold` rule.
  `.section-note` and ledes: IBM Plex Serif, `--ink-muted`.
- **Radii stay small:** `--radius-sm` 2px (badges, chips), `--radius-md` 4px
  (buttons, inputs), `--radius-lg` 8px (cards, dialogs). Pills only for `.chip`.
- **Sample-data bar (`.sample-banner`):** `--warn-bg` with `--warn-ink` text and
  a 1px `--warn-border` bottom edge; keep `max-height: var(--space-8)`.
- **Dark mode** is Hive's Night theme: a navy ground (`--surface` #07101c), cards
  one step lighter, gold and Buzz accents. Selected per token, not inverted.

The instinct to avoid: a generic SaaS dashboard with a navy accent. Gold rule
under the bar, gold eyebrows, Diploma bands, Barlow headings and the one
chamfered gold button are what make it Georgia Tech. Use all five.

---

## 3. Colour tokens

Every value below is a literal in the `:root` block (Day) and the
`@media (prefers-color-scheme: dark) { :root { … } }` block (Night). Hive token
names are in brackets so you can trace each one in `docs/specs/hive/tokens.json`.

### Required names (keep the names, replace the values)

| App token | Day | Night | Hive source |
|---|---|---|---|
| `--ink` | `#051e39` | `#eaeff6` | `text` (GT Navy by day) |
| `--ink-muted` | `#615a4a` | `#bec8d6` | `text-muted` (`neutral-11`) |
| `--ink-subtle` | `#7b7461` | `#8997a8` | `neutral-10`; 4.65:1 on white, **use only on `--surface` / `--surface-raised`** |
| `--surface` | `#ffffff` | `#07101c` | `bg` |
| `--surface-sunken` | `#f9f6e5` | `#0c1723` | `bg-subtle` (GT Diploma by day) |
| `--surface-raised` | `#ffffff` | `#16212f` | `surface` |
| `--surface-hover` | `#ebe8df` | `#1e2a38` | `surface-hover` |
| `--line` | `#d8d4c8` | `#323e4e` | `border-subtle` |
| `--line-strong` | `#87806c` | `#7a8798` | `border-control` (≥3:1, for inputs) |
| `--backdrop` | `rgba(5, 30, 57, 0.55)` | `rgba(0, 0, 0, 0.6)` | navy scrim |
| `--accent` | `#004c97` | `#508ed9` | `navy-9` (GT Bright Blue): links, secondary button, focus ring |
| `--on-accent` | `#ffffff` | `#051e39` | `text-on-secondary` |
| `--error` | `#c22a63` | `#f39ab2` | `danger` (`azalea-11`) |
| `--warn-bg` | `#feeed2` | `#342301` | `warning-bg` (`buzz-3`) |
| `--warn-border` | `#eaaa00` | `#eaaa00` | `gt-buzz` |
| `--warn-ink` | `#896306` | `#e6bf6a` | `warning` (`buzz-11`) |

### New tokens to add (names chosen to pass the guard greps)

Any new name containing `ink|surface|accent|line|error|warn|status|backdrop` must
be declared in both blocks **and** used at least once (§7a.2).

| App token | Day | Night | Hive source / use |
|---|---|---|---|
| `--gold` | `#b39051` | `#b39051` | `gt-gold`: rules, eyebrow bar, active-tab underline |
| `--gold-ink` | `#886a36` | `#debd88` | `text-gold` (`gold-11`): gold text, weight ≥500 |
| `--action-primary` | `#b39051` | `#b39051` | `action-primary` |
| `--action-primary-hover` | `#c29d5b` | `#c29d5b` | `gold-10` |
| `--on-action-primary` | `#051e39` | `#051e39` | `text-on-gold`: always navy |
| `--accent-hover` | `#003f7c` | `#5f9eea` | `navy-10` |
| `--chrome` | `#051e39` | `#0c213a` | `surface-brand`: the app bar |
| `--on-chrome` | `#ffffff` | `#eaeff6` | `text-on-brand` |
| `--focus-on-chrome` | `#eaaa00` | `#eaaa00` | `focus-ring-inverse` (Buzz) |
| `--surface-selected` | `#f5e6cd` | `#322713` | selected row / active nav tint |

The focus ring stays exactly `outline: 2px solid var(--accent)` (a test checks
the string) with `outline-offset: 2px`. Inside `.site-header`, override with
`outline-color: var(--focus-on-chrome)`.

---

## 4. Status, milestone, availability and priority colours

### The six statuses (schema vocabulary — never add a seventh)

Status values come from `db/schema.sql` via `app/status.py`. Restyle them to
Hive's status tokens; the words are unchanged. Every status shown anywhere
carries its word; that is the colour-blind mitigation, so never show a status
as colour alone.

| Class | `--status-*` (ink and bar fill), Day / Night | Badge background `--status-*-bg`, Day / Night |
|---|---|---|
| `status-on-track` | `#007870` / `#7cc2ba` (Campanile) | `#dcf7f3` / `#032d2a` |
| `status-at-risk` | `#896306` / `#e6bf6a` (Buzz) | `#feeed2` / `#342301` |
| `status-off-track` | `#c22a63` / `#f39ab2` (Azalea) | `#feeaee` / `#470c21` |
| `status-not-started` | `#615a4a` / `#bec8d6` (neutral) | `--status-neutral-bg`: `#f2f0ea` / `#16212f` |
| `status-paused` | `#615a4a` / `#bec8d6` (neutral) | `--status-neutral-bg` |
| `status-complete` | `#003d69` / `#a5cbfa` (Medium Navy) | `#e7f3f6` / `#1a292d` (Burdell) |

Token names to add: `--status-on-track-bg`, `--status-at-risk-bg`,
`--status-off-track-bg`, `--status-neutral-bg`, `--status-complete-bg`.

- `.badge.status-*`: background `--status-*-bg`, text `--status-*`, weight 500,
  `--radius-sm`. Every ink clears 4.5:1 on its background in both themes.
- `.bar-fill.status-*`, `.count.status-*`, `.connection-status.status-*`: use
  `--status-*` as the fill or text colour.
- Not started and Paused share an ink. Their words tell them apart; keep it.

**Milestones** (`.oct16-mstatus.m-*`, from `oct16_data.OUTCOMES`):
`m-met` → `--status-on-track`; `m-in-progress` → `--accent`;
`m-not-started` → `--status-not-started`; `m-due-dec` → `--warn-ink`;
`m-confirm` → `--status-at-risk`. Same badge treatment as status badges.

**Availability** (`.availability-*`, from `oct16_data.DATA_REQUIREMENTS`):
`availability-have-it` → `--status-on-track`; `availability-derived` →
`--accent`; `availability-partial` → `--status-at-risk`; `availability-build` →
`--warn-ink`; `availability-no` → `--status-off-track`.

### The six priority keys

One key colour per priority code, used only to identify P01–P06 (the inline
`--priority` custom property on cards and chips). Hive validated this set: worst
adjacent pair ΔE 10 under protanopia/deuteranopia, 18 for normal vision, and at
least 11.1 (ΔE, OKLab ×100) from every status ink in both themes, so a priority
does not read as a status.

| Token | Day | Night | Hue (Hive source) |
|---|---|---|---|
| `--priority-1` | `#051e39` | `#7f9cc0` | Navy (`gt-navy`; lifted at night so it shows on the navy ground) |
| `--priority-2` | `#92398f` | `#a955a5` | Plum (`chart-5`, from GT Whistle) |
| `--priority-3` | `#b2852e` | `#b78934` | Gold (`chart-2`, from GT Gold) |
| `--priority-4` | `#1762b6` | `#4087de` | Blue (`chart-1`, from GT Bright Blue) |
| `--priority-5` | `#d8662a` | `#d8662a` | Ember (`chart-4`, Hive addition) |
| `--priority-6` | `#299abe` | `#32a0c5` | Sky (`chart-7`, from GT Burdell) |

`--priority-5` Night equals Day; that is intended (it clears 3:1 on both grounds).
The dark block must still declare it (§7b.11).

---

## 5. Typography

Self-host these ten woff2 files (SIL Open Font License; copy from
`docs/specs/hive/fonts/`, with the two `LICENSE-*.txt` files):

| Family | Files | Weights |
|---|---|---|
| Barlow | `barlow-500.woff2`, `barlow-600.woff2`, `barlow-700.woff2` | 500, 600, 700 |
| IBM Plex Sans | `ibm-plex-sans-400.woff2`, `-500`, `-600` | 400, 500, 600 |
| IBM Plex Serif | `ibm-plex-serif-400.woff2`, `ibm-plex-serif-400-italic.woff2` | 400, 400 italic |
| IBM Plex Mono | `ibm-plex-mono-400.woff2`, `-500` | 400, 500 |

One `@font-face` per file, `font-display: swap`, `src: url("/static/fonts/<file>") format("woff2")`.

Family tokens (in `:root`, not colour so no dark override needed):

```css
--font-display: "Barlow", "DIN 2014", Roboto, system-ui, sans-serif;
--font-sans: "IBM Plex Sans", "Adelle Sans", Roboto, system-ui, -apple-system, "Segoe UI", sans-serif;
--font-serif: "IBM Plex Serif", "Adelle", "Source Serif 4", serif;
--font-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
```

Georgia is removed everywhere. `body` uses `var(--font-sans)`; `h1` and `h2` use
`var(--font-display)` (this needs the test edit in §8). Use
`font-variant-numeric: tabular-nums` in tables, bars' labels and counts.

Type scale (every `font-size` in the sheet is a `var(--text-*)`):

| Token | Value | Hive style |
|---|---|---|
| `--text-xs` | `0.75rem` (12px) | `caption`, eyebrow |
| `--text-sm` | `0.875rem` (14px) | `body-sm`, `label`, table cells |
| `--text-base` | `1rem` (16px) | `body` |
| `--text-lg` | `1.125rem` (18px) | `heading-4`, card titles |
| `--text-xl` | `1.375rem` (22px) | `heading-3` |
| `--text-2xl` | `1.75rem` (28px) | `heading-2` |
| `--text-3xl` | `2.25rem` (36px) | `heading-1` |
| `--text-stat` (new) | `2.5rem` (40px) | `stat-xl`, the `.stat-value` number |

Line heights: headings 1.15–1.2, body 1.5, tables 1.4.

---

## 6. Spacing, radius, shadow, motion

```css
--space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
--space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem;
--radius-sm: 2px; --radius-md: 4px; --radius-lg: 8px; --radius-pill: 999px;
--chamfer-sm: 8px;
--duration-fast: 120ms; --ease-standard: cubic-bezier(0.2, 0, 0, 1);
```

Shadows are colour literals, so they live in the token blocks:

| Token | Day | Night |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(5, 30, 57, 0.08)` | `0 1px 2px rgba(0, 0, 0, 0.5)` |
| `--shadow-md` | `0 4px 12px rgba(5, 30, 57, 0.10)` | `0 4px 12px rgba(0, 0, 0, 0.55)` |
| `--shadow-lg` (new) | `0 12px 32px rgba(5, 30, 57, 0.14)` | `0 12px 32px rgba(0, 0, 0, 0.6)` |

Honour `prefers-reduced-motion: reduce` (no transitions).

---

## 7. The guard tests your output must pass (unchanged except §8)

Verified against the tests in `tests/` at commit `64a0894`.

### 7a. `test_design_system.py`

1. No `#hex` or `rgba(` outside a `:root {` block. Token blocks are found by a
   line that is exactly `:root {` after trimming, so the dark block must be
   `@media (prefers-color-scheme: dark) {` then `  :root {` on its own line.
   Comments are stripped before the check.
2. Every token whose name contains `ink|surface|accent|line|error|warn|status|backdrop`
   is declared and used; every `var()` is declared.
3. `--space-1…4`, `--radius-sm/md/lg`, `--text-xs/sm/base/lg`, `--shadow-sm/md` exist.
4. Each such colour token in `:root` is redeclared in the dark block.
5. No `font-size: <n>rem` outside tokens.
6. Rules exist for `.card-modal .card-body .badge .bar .bar-fill .initiative-row
   .tile .button .error-page .breadcrumb .toast .drawer .empty .chip .field`.
7. `.button.primary`, `.button.secondary`, `.button.ghost` exist.
8. A rule for each schema status class; the string `status-done` never appears.

### 7b. `test_visual_system.py`

9–11. `--priority-1…6` in `:root`, all distinct, each redeclared in the dark block.
12. No priority literal equals a status literal (guaranteed by §4's values).
13. `^h1 {` and `^h2 {` rules at line start contain the heading-font var (see §8).
14. A `body {` rule contains `var(--font-sans)`.
15. `.eyebrow`, `.section-heading`, `.section-note` have rules.

### 7c. Behaviour, navigation, verification

17. Exact strings: `@media (max-width: 640px)`,
    `@media (min-width: 641px) and (max-width: 1024px)`, `@media (min-width: 1025px)`.
18. `overflow-x: hidden` appears.
19. `.nav-toggle:checked ~ .site-nav` appears.
20. `:focus-visible` and `outline: 2px solid var(--accent)` appear.
21. `overflow: hidden` appears (for `body.overlay-open`).
22. The `.sample-banner { … }` rule contains `max-height: var(--space-8)`.
23. A `@media print { … sample-banner … }` block in `style.css`.
24. **`style.css`** contains `@media print` and the literal
    `.site-nav, .nav-toggle-label { display: none; }` (`test_navigation.py` reads
    `style.css` only; the earlier brief wrongly said print.css would do).
25. `print.css` exists and mentions `.site-header` and `.site-nav`.
26. `@media (max-width: 900px)` or `@media (max-width: 1024px)` appears.
31–32. `--surface:` and `--accent:` declared; the literal `prefers-color-scheme: dark` appears.

### 7d. `test_status_presentation.py`

27. `.badge.status-*` rule for all six statuses.
28. A rule for every milestone class the data emits: `.m-confirm .m-due-dec
    .m-in-progress .m-met .m-not-started`.
29. A rule for every availability class: `.availability-build -derived -have-it -no -partial`.

---

## 8. Test edits this restyle requires

These were dry-run before handoff: the §3–§6 token values, the new tokens, `--font-display` on `h1`/`h2` and these two edits pass all 74 guard tests in the seven files of §7.

Hive's headings are Barlow, a sans display face, not a serif. Two edits, made in
the same change and called out in the commit message:

1. `tests/test_visual_system.py::test_headings_use_the_serif_token`: rename to
   `test_headings_use_the_display_token` and assert `var(--font-display)` in the
   `h1 {` and `h2 {` rules.
2. `tests/test_visual_system.py::test_font_family_tokens_exist`: also assert
   `--font-display` in `:root` (keep the `--font-serif` and `--font-sans` checks;
   `--font-serif` stays, now IBM Plex Serif, for ledes and reading text).

Update the "serif headings" wording in the `style.css` header comment and in
`docs/specs` where it describes the split. No other test changes. If any other
test fails, fix the CSS, not the test.

---

## 9. Classes the templates emit with no rule today

These 56 classes appear in templates but have no selector in the current sheet.
Most need nothing; style the ones that carry meaning (at minimum `attention*`,
`card-*`, `diary*`, `panel*`, `progress-*`, `update-*`, `danger`, `needs-update`):

`admin-actions age attention attention-list card-actions card-code
card-connections card-description card-diary card-fullpage card-latest
card-owner card-tags card-title changes check checks-clear connection-owner
connections danger dean-rows detail-header diary diary-by diary-date diary-note
diary-percent diary-status footer-note goal-mis level mi-row needs-update
oct16-outcome-status oct16-tradeoff-text panel panel-heading
person-initiatives priority-fields priority-link progress-fill progress-track
row-main row-owner row-progress search-label since-form slider-row tags
tags-label team-link text-button update-button update-form update-form-body`

Also emitted dynamically: `oct16-{id}` per outcome, `pro` / `con` on
`.oct16-tradeoff`, and the status, milestone and availability classes above.
Classes present in the sheet but not found in templates (for example
`availability-*`, `m-*`, `status-*`, `tile*`, `drawer-close`, `modal-close`,
`overlay-open`) are emitted from Python or JavaScript: **keep them.**

---

## 10. Print

Keep everything `print.css` does today (hide `.site-header`, `.site-nav`,
`.whoami`, `.switch`, `.brand`, `.card-modal`, `.no-print`; 15mm margins; rows
don't split). Apply Hive's document rules: white page, navy ink (`#051e39`), IBM
Plex Sans for UI text, 11pt body, a 3px GT Gold rule under the page title,
tables with a 2px navy header rule and hairline rows. `print.css` is not
scanned for literals, but prefer tokens where they resolve.

`style.css` must also keep its own `@media print` block hiding `.sample-banner`,
`.meeting-controls`, `.presenter` and `.no-print`, with the exact
`.site-nav, .nav-toggle-label { display: none; }` line.

---

## 11. Recorded deviations from GT's brand guide (keep these comments in the CSS)

- **Dark Gold text** is `#886a36`, not GT's `#8F713D`: darkened about 2% so gold
  text also clears 4.5:1 on Diploma (`#8F713D` is 4.21:1 there; `#886a36` is 4.65:1).
- **Bright Blue** (`#004C97`), **Medium Navy** and **Light Gold** are
  gradient-only in GT's guide; Hive promotes them to the interactive blue, the
  Complete status and night-mode gold text.
- **Fonts:** GT names DIN/Adelle for print and Roboto for web. Hive uses Barlow
  (DIN lineage) and IBM Plex (GT's own named web alternate for Adelle).
  Roboto remains in every fallback stack.
- **Status colours** move from the prototype's generic green/amber/red to GT
  Campanile, Buzz and Azalea with neutral and navy, each tuned for 4.5:1.
- **Ember** (`#d8662a`, `--priority-5`) is a Hive addition; GT has no orange.
- **Gradients** are retired in product UI.
- The old navy `#003057` and the prototype priority colours (`#53d7e8`,
  `#f2b84b`, `#9a8cff`, `#ff7f6e`, `#42d39b`, `#ef8ad2`) are gone.

---

## 12. Acceptance

- [ ] `pytest` passes in full, with only the two test edits in §8. Exception: `tests/test_oct16_swap.py::test_dry_run_reports_a_no_op_as_a_no_op` and `::test_the_swap_does_not_change_layout` already fail on a clean checkout of `64a0894` (Linux, Python 3.13); they do not touch CSS. Leave them as they are and say so in the PR.
- [ ] `grep -nE '#[0-9a-fA-F]{3,8}|rgba?\(' app/static/style.css` matches only
      inside the two token blocks or comments.
- [ ] Every colour token in §3–§4 exists in both blocks with the values given.
- [ ] Ten woff2 files in `app/static/fonts/`; no `http` URL anywhere in either sheet.
- [ ] Georgia, Roboto Slab, `#003057` and the old priority hexes are gone.
- [ ] `docs/specs/hive/style-guide.html` renders every token, the six status
      badges, the six priority keys, buttons, fields, cards, tables, the app bar,
      in Day and Night (toggle `data-theme` or use the OS setting).
- [ ] Screenshots of `/`, `/goals/1`, `/oct16` and a card modal in both themes,
      attached to the PR.
- [ ] **Lineage:** with no logo, a GT person recognises it: navy bar with the gold
      rule, gold eyebrows, Diploma bands, Barlow headings, one chamfered gold
      button.
- [ ] **Modernity:** it reads as software made in 2026.
- [ ] Any further deviation from this brief is listed in the PR description.
