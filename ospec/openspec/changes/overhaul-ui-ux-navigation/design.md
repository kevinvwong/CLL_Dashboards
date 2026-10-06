## Context

The app is server-rendered FastAPI with Jinja2 and htmx, running at
`127.0.0.1:8000`. Interactions are partial-page swaps; the initiative card is
loaded into a `<dialog id="card-modal">` and rows carry `hx-get` onto it.
The Outcomes page (`/oct16`) is the most finished screen and becomes the visual
reference. Users are the Dean (Bill), team leads (Elizabeth, Mario, Tim), and the
Associate Director, Strategic Operations (Kevin).

This design was first written against the running app (`/oct16` render, card
modal behaviour, JSON error bodies). The claims were then verified against the
source on 2026-10-06 — see `proposal.md` → What Changes for which were confirmed
and which were retargeted.

## Goals / Non-Goals

- Goals:
  - One visual language, extracted from the Outcomes page.
  - Every entity reachable from the nav and from search.
  - Fast update entry.
  - A meeting view that runs the meeting.
  - Usable at the side-panel width (~726px) and on mobile.
- Non-Goals:
  - Changing the data model or permissions model.
  - KPI computation.
  - Authentication. Switch user stays a prototype affordance.

## Decisions

- **The Outcomes page is the design source.** Its pill, card, and progress-bar
  styles are extracted into tokens and components, so no new style is introduced.
- **Partial vs. full responses.** Any endpoint that serves both a modal or drawer
  and a full page checks for a partial request header (`HX-Request` / `HX-Target`)
  and returns a fragment for partial requests, the full layout otherwise. This is
  the fix for two confirmed defects: `edit_details.html` currently `extends
  base.html`, so the whole layout loads into the modal; and `card_full.html`
  includes `_card_body.html`, which carries the modal close control, so the
  standalone page shows both "← Back" and "×".
- **Drawer over modal for initiative detail.** The user keeps the list context.
  The URL updates (`/initiatives/{id}`) so the view can be shared. Loading that
  URL directly renders a full page.
- **Filter state in the query string.** Views can be shared and bookmarked. No
  client-side store is needed.
- **Status scale follows the schema, not a new vocabulary.** The statuses are the
  schema's `CHECK`: `Not started`, `On track`, `At risk`, `Off track`, `Complete`,
  `Paused`. The original scale table listed "Done", which the schema cannot store,
  and omitted `Complete` and `Paused`. Colour is never the only signal; every
  status carries its text label.

  | Status (schema value) | Color |
  |---|---|
  | On track | green |
  | At risk | amber |
  | Off track | red |
  | Not started | grey |
  | Complete | dark green |
  | Paused | grey |

  This is the vocabulary `status-presentation` (in `deepen-dashboard-modules`)
  already defines and reads from `db/schema.sql`. Introducing "Done" here would
  re-create the drift that capability exists to prevent.
- **Stale threshold** defaults to 14 days and is configurable in one place,
  matching the existing `STALE_DAYS` / `ATTENTION_STALE_DAYS` constants.
- **"Last meeting date"** is the most recent meeting date stored or configured.
  If none exists, it falls back to 7 days ago.
- **Empty-side chrome is suppressed, not reordered.** `list.html` renders its
  Dean list and the "D-1" divider unconditionally. The fix is to render each side
  only when it has rows, so a Dean-only or D-1-only slice does not leave an empty
  `<ul>` or a divider pointing at nothing. (The recorded symptom, "headers render
  in the wrong order", did not reproduce: the order is already header-then-group.)

## Open Questions

- Which roles may edit owner, goals and priorities, and tier? Only the owner and
  admins, or anyone?
- Is there a canonical "meeting date" record, or should the app store one each
  time a meeting is run?
- Should the sample-data banner be dismissible per session or per user?
- Is "Done" wanted as a status? If so, it is a separate schema change, not a
  design-system change.

**Assumed on import (default, reversible):** whether this change supersedes the
four open changes or sits alongside them. It is written as **alongside** — their
capabilities are amended, not replaced, and every delta here is `ADDED` because no
main specs exist yet. This is the non-destructive default, not an explicit ruling;
if it is reversed, those changes should be closed and their capabilities folded
in, and the deltas rewritten as `MODIFIED` after archiving.

## Risks / Trade-offs

- Restyling every template at once risks regressions. Mitigation: ship the tokens
  and components first (task group 2), then migrate one page at a time.
- Presenter mode adds a second layout to maintain. Mitigation: it reuses the
  meeting fragments with a larger-type modifier class.
- The search index is built per request from the database. Acceptable at the
  current size (<100 initiatives). Revisit above roughly 1,000.
- Two capabilities would own the status scale (`status-presentation` and
  `design-system`) if the non-goal above is not honoured. Mitigation: the
  design-system delta adds components and tokens and references the existing
  vocabulary rather than restating it.

## Migration Plan

1. Ship the bug fixes behind no flag.
2. Add new routes. Make `/oct16` return a 301 redirect to `/outcomes`.
3. Migrate templates page by page to the shared components.
4. Remove the legacy styles once no template references them.
