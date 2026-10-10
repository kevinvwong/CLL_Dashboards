# Design: fix-fullpage-card-duplication

## Decision 1 — suppress the fragment's header, keep the page's

Two ways to fix the duplicated title:

- **A:** delete the page's `section-heading` and let the fragment's `card-title`
  become the heading.
- **B:** suppress the fragment's `card-code`/`card-title` on the full page and
  keep the `section-heading`.

**B is right.** The page needs an `h1` for the route, and the section-heading
already carries the eyebrow (code · level), the `h1`, and the source-target chip
that has no equivalent in the fragment. Deleting it would leave the full page
with no `h1` at all — trading a duplication for a worse defect. B also leaves
the fragment untouched for the drawer, which genuinely needs its own header.

The mechanism already exists and is used one block above: the close control is
gated on `{% if modal is not defined or modal %}`. The drawer (`card.html`)
includes the fragment without setting `modal`, so `modal is not defined` is true
and the control shows; `team_initiative.html` includes it inside
`{% with modal=False %}`, so it hides. The header block joins that same
condition — no new flag, no new plumbing.

## Decision 2 — the heading must MOVE, not just stop repeating

Suppressing the duplicate title alone would leave the inverted outline intact:
the `h1` would still sit ~950px below the card body. So `section-heading` is
moved **above** the fragment include in `team_initiative.html`.

This is the part that makes the fix worth doing rather than cosmetic — an
assistive-technology user meeting the `h1` last is reading a document whose
structure contradicts its content.

## Decision 3 — remove the lower duplicates, not the upper ones

For the description and the "Contributes to" list, the **fragment's** copy is
kept and the page's removed:

- **Description** — byte-identical between `initiative_card` and
  `team_initiative_detail` for all 29 active initiatives. Identical data, so
  either copy goes; the fragment's is the one the drawer also uses, so removing
  the page's keeps a single renderer.
- **"Contributes to"** — the Dean set matches by name for all 29, but the copies
  are *not* equally useful: the fragment's renders `D27-1`, `D27-2`, `D27-4` as
  links with owner/status/progress slots; the page's renders bare titles. Remove
  the weaker copy.

Verified rather than assumed, because a mismatch would mean these are two
different datasets and removing one would lose information:

| Check | Result |
|---|---|
| description identical, 29 initiatives | 0 mismatches |
| Dean "Contributes to" set by name, 29 initiatives | 0 mismatches |
| fragment's copy carries the linkable code | true for all |

## Decision 4 — the regression test counts occurrences, not presence

The existing assertions pin the *drawer* (`test_cards.py` with `HX-Request`) and
the *presence* of "Contributes to" on the full page — both survive this change,
which is why they were not red before.

The new test therefore asserts the negative property that would have caught the
bug: each duplicated string appears **exactly once** on the full page. "Present"
is what the old tests checked and what let the duplication ship.

## Risk

Low and contained. Two templates plus a test. The risk is that a reader
depended on the removed names-only list — but it is a strict subset of the kept
copy, so nothing becomes unreachable. The `h1` move changes visual order, not
content; a screenshot comparison of the drawer is the check that it did not.
