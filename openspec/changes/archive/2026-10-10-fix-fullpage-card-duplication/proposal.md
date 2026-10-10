# Proposal: Fix the full-page card's duplicated header and inverted heading order

## Why

`/team-initiatives/{code}` renders the shared card body **and then** a second copy
of its header ~950px further down. Measured on the live page for MI-001, four
separate duplications:

| Duplicated | Both copies | Measured |
|---|---|---|
| Title | `h2` (card body) **and** `h1` | both "Portfolio & pathways", at y=269 and y=1217 |
| Code + level | `card-code` **and** `eyebrow` | "MI-001 Team Initiative" vs "MI-001 · Team Initiative" |
| Description | `card-description` **and** `mi-description` | identical paragraph, phrase count = 2 |
| "Contributes to" | `h3` (with codes) **and** `h2` (names only) | same three Dean initiatives |

The consequence is worse than redundancy. The page's only `h1` is rendered
**after the content it titles** (`docOrderInverted: true` — the `h2` at y=269
precedes the `h1` at y=1217). The document outline is inverted: an assistive
technology or reader mode announces the page heading last. The lower copies are
also the *less* informative ones — the page's "Contributes to" shows bare names
while the card body's carries `D27-1` / `D27-2` / `D27-4` codes and links.

`team_initiation.html` was assembled by appending the register's edges below a
shared fragment (`_card_body.html`) that was written for the drawer. The fragment
carries the header the drawer needs; the page added a second one rather than
suppressing the first.

## What Changes

- **`app/templates/_card_body.html`** — gate the fragment's own
  `card-code` + `card-title` block on the drawer condition already used for the
  close control (`modal is not defined or modal`). The drawer keeps them; the
  full page no longer repeats them.
- **`app/templates/team_initiative.html`** — move the `section-heading`
  (eyebrow + `h1` + source-target chip) **above** the card body so the page's
  heading leads its content, and remove the two blocks that duplicate what the
  fragment already renders: the `mi-description` paragraph and the `dean_links`
  "Contributes to" section.
- **Tests** — the two assertions that pin the affected structure
  (`test_cards.py` fragment-vs-full-page, `test_dean_layer.py` description and
  Dean links) are checked against the new shape, and a regression test asserts
  each duplicated string appears **exactly once** on the full page.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rev2-store`: the full-page initiative card renders one header, once, ahead of
  its content.

## Impact

- **`app/templates/_card_body.html`**, **`app/templates/team_initiative.html`**,
  **`tests/`** (regression coverage). No route, query, schema or CSS change.
- The drawer is unaffected: `card.html` includes the fragment without setting
  `modal`, so `modal is not defined` remains true and its header stays.
- Verification before syncing: the description is byte-identical between
  `initiative_card` and `team_initiative_detail` for all **29** active
  initiatives, and the "Contributes to" Dean set matches by name for all 29 —
  so both blocks are strict duplicates, not different data. That check is
  re-run as a task rather than asserted from memory.
