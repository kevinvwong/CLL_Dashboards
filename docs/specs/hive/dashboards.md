# Dashboards

A Hive dashboard answers its audience's top question in the first row and lets them drill down from there.

## Frame

- AppHeader (navy, sticky) across the top; SideNav on Diploma at the left, collapsing to the 64px rail below `bp-lg` and to a menu below `bp-md`.
- Content on `bg` (white by day), max width `content-max`, padding `space-6`; sections separated by `space-8`.
- Page order: Breadcrumbs (if nested) → page title (`heading-1`) with one primary action → data-freshness `info` Alert if relevant → filters → KPI row → charts → detail table.

## Layout

- KPI row: 3–5 StatTiles in `hv-dash-grid`. Each tile shows the value, signed change, and what it is compared with.
- Charts: ChartCards on a 12-column grid with `space-4` gutters; full width for time series, half width for comparisons. Never more than two charts per row on laptops.
- Detail: one DataTable at the bottom, sortable, `default` density, paginated at 25 rows.

## Filters and scope

- Scope selectors (fiscal year, unit) and FilterChips in one row above everything they affect, ordered time → scope → status.
- Filters apply to every chart and table on the page and persist across Tabs.
- Show the active scope in the page subtitle ("FY2026 · All units") so screenshots and exports carry it.

## States

- Loading: Skeletons shaped like the final tiles and charts; no layout shift when data arrives.
- Empty: EmptyState with the reason and one action. Filtered-empty offers "Clear filters".
- Error: a `danger` Alert in place of the affected card; the rest of the dashboard still renders.

## Density

`row-default` tables and `control-md` controls by default. Analyst views may switch tables to `compact`; never shrink text below `body-sm`.

## Status and priority vocabulary

Initiative status comes from the dashboard database and has exactly six values. Use these words, tokens and icons everywhere; never add a seventh:

| Status | Ink / fill | Badge background | Icon |
| --- | --- | --- | --- |
| On track | `status-on-track` | `status-on-track-bg` | circle-check |
| At risk | `status-at-risk` | `status-at-risk-bg` | triangle-alert |
| Off track | `status-off-track` | `status-off-track-bg` | circle-x |
| Not started | `status-not-started` | `status-neutral-bg` | circle-dashed |
| Paused | `status-paused` | `status-neutral-bg` | circle-pause |
| Complete | `status-complete` | `status-complete-bg` | badge-check |

Each of the six strategic priorities (P01–P06) has a key colour, `priority-1` to `priority-6`: Navy, Plum, Gold, Blue, Ember, Sky. Priority colours mark identity (a stripe on a card, a swatch beside the code) and never mean state; status colours never key a priority.
