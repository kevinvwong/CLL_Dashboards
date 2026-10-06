Hive is a product design system descended from the Georgia Tech brand (2026–27 color standards). It keeps GT's white-and-gold identity recognizable while adding what a modern UI system needs: 12-step color scales, semantic tokens, a dark theme, accessible pairings by construction, and components. Use it for the CLL dashboard app and the presentations and documents that come out of it; use the official GT brand guide for signage, merchandise and anything carrying an official GT logo. Sections: Data visualization, Dashboards, Presentations and documents.

## Principles

1. **White and gold lead; navy steadies.** Light surfaces are `bg` (white) and `bg-subtle` (Diploma). Gold appears as the primary action, the gold rule and eyebrows. Navy is the ink (`text`) and the feature band (`surface-brand`).
2. **Lineage is fixed, evolution is explicit.** Every GT color lives unchanged as a `gt-*` token. Scales and semantic tokens may evolve; `gt-*` values never do. Any value that departs from GT says so in its usage note.
3. **Accessible by construction.** Every text token names the grounds it reads on and clears 4.5:1 there in both themes. Status always pairs color with an icon and a word.
4. **Engineered, warm.** Small radii, square brand bands, one 30° chamfer as the signature, serif ledes for the human voice.

## Lineage

How each GT brand element maps into Hive. **Exact** = same value; **Evolved** = derived with a stated reason; **New** = Hive addition.

| GT brand element | Hive token(s) | Status | Why |
| --- | --- | --- | --- |
| Gold #B39051 | `gt-gold` → `gold-9`, `action-primary`, `border-accent` | Exact | Primary action and gold rule. |
| Dark Gold #8F713D | `gold-11` #886a36, `text-gold`, `border-primary` | Evolved | Darkened 2% so gold text clears 4.5:1 on Diploma as well as white. |
| Light Gold #DEBD88 | `gold-7` (day), `gold-11` (night) | Exact, promoted | GT reserves it for gradients; Hive uses it as hover border and night-mode gold text. |
| Navy #051E39 | `gt-navy` → `navy-12`, `text`, `text-on-gold`, `surface-brand` | Exact | All body ink and all ink on gold. |
| Medium Navy #003D69 | `navy-11`, `info` | Exact, promoted | Gradient-only in GT; Hive's informational text. |
| Bright Blue #004C97 | `navy-9`, `link`, `action-secondary`, `focus-ring` | Exact, promoted | Gradient-only in GT; becomes the interactive blue (8.5:1 on white). |
| White | `gt-white`, `bg`, `surface` | Exact | Light-theme page. |
| Diploma #F9F6E5 | `neutral-2`, `bg-subtle` | Exact | Section bands and stripes. |
| Buzz #EAAA00 | `buzz-9`, `highlight`, `warning-bg`, night `focus-ring` | Exact | Highlight and warning; navy ink only. |
| Campanile, Azalea, Tech Lawn, Whistle, Burdell | `campanile-*`, `azalea-*`, `techlawn-*`, `whistle-*`, `burdell-*` | Exact at step 9 | Accents ≤10% of a layout, as GT requires. Campanile carries success, Azalea carries danger. |
| Gold and navy gradients | none | Retired in UI | Flat fills only in product UI. Gradients remain a print and marketing device. |
| DIN 2014 / DIN Next Slab | `display` family: Barlow | Evolved | Open-source grotesk with the same signage and engineering roots; DIN 2014 is listed as the first fallback for licensed machines. |
| Adelle / Adelle Sans | `serif`: IBM Plex Serif, `sans`: IBM Plex Sans | Exact (GT's free alternates) | GT names Plex as Adelle's web alternate. Plex Sans replaces Roboto as the UI face. |
| Roboto / Roboto Slab | fallback only | Evolved | Kept in the stacks for continuity; not loaded. |
| Hexagon, mosaic tiles | `chamfer-*`, `angle-facet`, Patterns | Evolved | The hex facet becomes a 30° cut corner on primary buttons and feature cards. |
| Hive, dot matrix, pinstripe patterns | Patterns asset group | New construction | Original Hive drawings of the shapes GT describes. |
| Night theme | `dark` theme | New | Navy ground, gold and Buzz accents. |
| Chart palette | `chart-1`–`chart-8`, `seq-*`, `div-*` | Evolved | GT hues re-stepped to equal weight and validated for color-vision deficiency; Ember added. |
| Icons | Lucide subset (Icons group, `Hive.Icon`) | New | GT has no UI icon set. |

## Color

Each family is a 12-step scale: 1–2 backgrounds, 3–5 component fills (rest, hover, pressed), 6–8 borders, 9–10 solid fills, 11–12 text. In product code use **semantic tokens only**; `gold-*`, `navy-*`, `neutral-*` and `gt-*` are primitives for building semantics.

- Page `bg`, alternating bands `bg-subtle`, cards and inputs `surface`, wells `surface-sunken`.
- Body and headings `text`; secondary copy `text-muted`; gold labels `text-gold` at weight 500 or more (GT's rule for brand-colored text).
- Navy feature bands: `surface-brand` with `text-on-brand`; inside them, focus uses `focus-ring-inverse`.
- Primary action `action-primary` with `text-on-gold` and a 1px `border-primary`. Never white text on gold.
- Links `link`, underlined; hover `link-hover`.
- Status: `success` / `success-bg`, `danger` / `danger-bg`, `warning` / `warning-bg`, `info` / `info-bg`. Always add the icon and a word.
- Charts: `chart-1` to `chart-8` in order, never cycled; full rules in Data visualization.
- Proportion: white and Diploma dominate, gold and navy carry emphasis, accents stay under 10%.
- `border-accent` (gold on white, 2.99:1) is decorative. Pair it with weight or text whenever it marks state.

## Typography

- `display` (Barlow 600) for `display-xl`, `display-lg`, `heading-1`, `heading-2` and the uppercase `eyebrow`.
- `sans` (IBM Plex Sans) for UI and body: `heading-3`, `heading-4`, `body-lg`, `body`, `body-sm`, `label`, `caption`.
- `serif` (IBM Plex Serif) for `lede`, `quote`, `reading`: the human voice in stories and long reads.
- `mono` (IBM Plex Mono) for `code` and `numeric` tabular figures.
- Sentence case for headings, buttons and labels. Uppercase only in `eyebrow`.
- Fonts are self-hosted woff2 files in `fonts/` (Barlow 500/600/700; IBM Plex Sans 400/500/600; IBM Plex Serif 400 and italic; IBM Plex Mono 400/500), all SIL Open Font License. No external font requests.

## Shape, space and motion

- Spacing is a 4px scale: `space-1` (4) to `space-24` (96). Card padding `space-6`; section padding `space-16` desktop, `space-12` mobile.
- Radii stay small: `radius-md` for controls, `radius-lg` for cards, `radius-none` for brand bands and images.
- The chamfer is the signature: `chamfer-sm` on the primary button's top-right corner, `chamfer-md` on feature cards, `chamfer-lg` on hero bands. One chamfered element per region.
- Diagonals use `angle-facet` (30°).
- Elevation: `shadow-sm` inputs, `shadow-md` menus, `shadow-lg` dialogs only. Cards use borders, not shadows.
- Motion: `duration-fast` with `ease-standard` for hover and press; `duration-moderate` for menus; `duration-slow` for panels. Honor reduced motion.
- Focus: 2px solid `focus-ring`, 2px offset, on every interactive element.

## Content

Follow GT's editorial style guide and the motto "Progress and Service". In product UI:

- Verb-first buttons: "Apply now", "Request info", "Save changes".
- Errors state the fix: "Choose Spring, Summer or Fall."
- Say "Georgia Tech" in copy; follow GT naming standards for units ("College of Lifetime Learning").
- Use the dashboard status words exactly: On track, At risk, Off track, Not started, Paused, Complete.
- Numbers: thousands separators, units in labels not cells, "FY2026" for fiscal years, dates as "Oct 30, 2026".
- No exclamation marks in UI, no emoji.

## Iconography

Lucide line icons (ISC license): 24px grid, 2px stroke, round caps, in `currentColor`. Use `Hive.Icon` in code; the Icons asset group holds navy-inked SVGs for slides and documents. 16px in tables and small controls, 20px in buttons and navigation, 24px in empty states. Always beside a text label, or with an `aria-label` when alone. No emoji.

## Logos and patterns

Hive ships no logo. Use official files from brand.gatech.edu/brand-assets/logos and follow GT's logo rules; never redraw or recolor them. The Patterns group holds original Hive constructions (hive, dot matrix, 30° pinstripe) in GT Gold; use them behind content at no more than 20% of a layout.

## Evolution and governance

- `gt-*` tokens change only when GT publishes new standards; then update them and record the GT release in `tokens.json` `meta.lineageVersion`.
- Scales and semantics may evolve; each change keeps every contrast pair passing and notes its reason in the token's usage.
- New tokens or components need a stated need, a contrast check in both themes, and a usage note.
- Version: new tokens or components are minor; changed values are minor with a note; renames and removals are major.
