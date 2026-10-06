# Blueprint redesign — design

Date: 2026-10-06
Status: approved by the user, ready for planning

## Why

The dashboard is flat: every screen carries the same visual weight, there is no
structural hierarchy, and the only colour identity is a navy accent on white.
The Dean's own prototype (`cll-blueprint-2027.wag32002.chatgpt.site`) is a far
richer reference — a hero "blueprint stage", a Dean node fanning into six
colour-coded priority cards, panels, chips, a detail dialog, and a per-priority
colour scale.

This design adopts the prototype's **structure** (D3 + Nav-3 below) while
staying on Georgia Tech brand and keeping the app's actual job — the Wednesday
leadership meeting — intact.

## Decisions taken with the user

| Decision | Chosen | Alternatives considered |
|---|---|---|
| Scope | **Whole experience** (C) | visual reference only; content model too |
| Effect on open work | **Supersede** `overhaul-ui-ux-navigation` | redesign inside it; run alongside |
| Cascade data | **From Rev2** (C3) | our data restructured; adopt the prototype's model |
| Where the app reads | **Azure SQL** (C3b-i) | cascade-only; sync into SQLite |
| Source for everything | **β: Azure SQL for all data** | cascade layer only (α) |
| Sequencing | **Seq-1: design first, migrate later** | migrate first; both at once |
| Visual identity | **D3: dark chrome, light content** | prototype's dark blueprint; GT light |
| Screen set | **Nav-3: hybrid** | prototype-led; workflow-led |

**Seq-1** is the constraint everything else hangs from: the design lands now,
against Rev2's read models as a stable interface, with the app still reading
SQLite. The migration (β) is a separate follow-on change.

## Goals

- One visual language with real hierarchy: a hero stage, panels, cards, chips.
- Every screen rebuilt on a token-driven component set.
- The Wednesday meeting and the Outcomes page keep working and stay printable.
- The status vocabulary stays the schema's; the priority colour scale is adopted
  from the prototype, not invented.

## Non-Goals

- **The β migration.** Porting the 5 SQL modules off SQLite, re-pointing 17 test
  files, seeding Rev2 — a separate change.
- The prototype's KPI vocabulary. `config.yaml` says "Say 'initiative', never
  'KPI', in UI text"; this design keeps our words.
- New data model. Teams and team KPIs stay out until β.
- Authentication, permissions, the Rev2 schema.

## §1 — Visual system (D3)

Dark chrome over light content. Identity where it is seen; readability where it
is read, projected, and printed.

```
+--------------------------------------------------------------------+
|  DARK CHROME   GT Navy #003057, gold hairline #B3A369              |  header, nav, footer
+--------------------------------------------------------------------+
|  LIGHT CONTENT page #F7F8FA  card #FFFFFF  line #E3E6EA  ink #1A1D21|
+--------------------------------------------------------------------+
```

- **Accent** GT gold `#B3A369` for rules, active states, marks.
- **Type** serif (Georgia stack) for headings only; system sans for body. The
  serif/sans split is what gives the prototype its gravitas.
- **Status scale unchanged**, still read from `db/schema.sql`'s `CHECK`:
  on-track `#1b7f3b`, at-risk `#b26a00`, off-track `#c0392b`, not-started
  `#9a9a9a`, paused `#9a9a9a`, complete `#14532d`.
- **Priority colours adopted from the prototype** as a six-value token set:
  `#53d7e8`, `#f2b84b`, `#9a8cff`, `#ff7f6e`, `#42d39b`, `#ef8ad2` — used only
  as per-priority keys, never as status.
- Every value a token. `print.css` strips chrome, keeps content.

## §2 — Screen set (Nav-3) and surface per screen

The prototype's structural insight: the executive map is a **hero stage**, and
detail is a **dialog over it**. Kept.

| Screen | Becomes | Surface |
|---|---|---|
| `/` | **Blueprint** — Dean node → 6 priority cards → selected-priority panel → initiative-signals strip | page |
| `/goals/{n}`, `/priorities/{x}` | **Cascade** drill-down — priority → initiatives, grouped, relationships visible | page (+ drawer per initiative) |
| `/initiatives/{code}` | rebuilt card: header, facts, latest update, relationships, diary | **drawer** from a list; **full page** on direct load |
| `/initiatives` | index table, filterable | page |
| `/people`, `/people/{id}` | index + person portfolio | page |
| `/meeting` | same role, restyled | page, print-first |
| `/oct16` → `/outcomes` | same role, restyled (301 from `/oct16`) | page |
| `/checks` | checks + Coverage merged | page, admin |
| update form | slider + segmented status + previous value | in the drawer |
| edit details | owner, tags, tier, parent link | in the drawer |

**Rule:** anything reached from a list opens in the drawer; anything
bookmarkable has a full page. Same URL either way.

## §3 — Component system

The flatness is an absence of hierarchy. These components supply it, all
token-driven:

stage · panel · card (priority / goal / initiative) · chip · stat tile · pill ·
drawer · dialog · table · empty state · breadcrumb · toast.

Section headings adopt the prototype's **eyebrow → serif heading → note**
pattern; that single change does most of the de-flattening.

## §4 — Data seam

- **Design against** Rev2's read models (stable interface):
  `vw_goal_initiatives`, `vw_priority_initiatives`, `vw_strategy_traceability`,
  `vw_person_portfolio`.
- **Runtime today** SQLite, unchanged.
- **Migration** separate follow-on change (β).

### Superseding `overhaul-ui-ux-navigation`

- Carry over all 8 completed group-1 bug fixes (this design needs them).
- Carry over the 6 spec deltas, rewritten under the new nav.
- The deploy-zip and build-determinism commits are unaffected.

## §5 — Verification

- Visual regression at 375 / 726 / 1280px, light content and dark chrome.
- Keyboard pass on the drawer, filters, and search; focus returns on close.
- Print check on `/meeting` — the one screen that must not regress.
- Token check: no colour literal outside a token block.
- Status vocabulary still equals the schema's `CHECK`.
- Existing suite green (352 tests at design time).

## Risks / Trade-offs

- [Two palettes (chrome + content) can drift] → both are token blocks in one
  file, and the token test asserts no literal outside them.
- [Superseding an open change loses its context] → its completed work is carried
  over explicitly, and the change itself is not deleted, only closed.
- [Designing against read models the app does not yet read] → the models are
  live and tested (71 tests, 10/10 acceptance); β swaps the source under a
  design that already exists.
- [Dark chrome on a projector] → chrome is only the header, nav and footer;
  content surfaces stay light.

## Open Questions

- None blocking. Deferred to β: whether the cascade gains a team layer via the
  prototype's 29 team KPIs.
