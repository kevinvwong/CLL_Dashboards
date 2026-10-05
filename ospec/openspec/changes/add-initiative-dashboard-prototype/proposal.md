# Proposal

## Why

The Dean tracks college initiatives in a vibe-coded prototype (CLL Blueprint 2027) that only he can edit. Leaders cannot fix wrong links between initiatives, goals, and priorities, and the Dean has reported progress percentages owners never supplied. The team needs a usable prototype: the Dean runs Wednesday leadership meetings from it, and owners enter their own progress by Monday.

## What Changes

- A small web app (FastAPI, Jinja2, HTMX, SQLite) on the existing `db/schema.sql`, runnable with one command.
- Home screen with two entry points: 5 Strategy 2035 goal tiles and 6 annual-priority tiles.
- Goal and priority list screens: Dean initiatives above a divider, D-1 initiatives below grouped by owner, each with a progress bar.
- Initiative card (modal and full page): description, owner, tags, Feeds and Fed by links, latest progress, running diary.
- Person card with stale-update flags.
- Progress updates: percent slider, status, short note, appended to a diary; only owner, Dean, or admin can post.
- Admin editing in the app: descriptions, tags, primary flags, links, new and retired initiatives, with an audit log.
- Meeting page: what changed since last meeting plus an at-risk and stale list, print-friendly.
- Shared access: passcode gate, person picker, persistent storage, daily backups.
- Excel intake template and validated importer that preserves progress history on re-import.
- Data-checks page listing rule violations.

### Milestones

| Date | Milestone |
|---|---|
| Thu Oct 8, 2026 | Clickable demo with sample data: navigation, cards, updates |
| Fri Oct 9 | Admin editing and meeting page done; live on the VPS over HTTPS; template sent to leaders |
| Mon Oct 12 | Live data imported; owners enter first updates |
| Wed Oct 14 | First leadership meeting run from the meeting page |
| Fri Oct 16 | First dashboard delivered to the Dean |

**Out of scope**

- Single sign-on and real per-user accounts (passcode plus person picker only).
- Anything below D-1 initiatives: tasks, sub-projects, metrics, KPIs.
- Automatic rollup of D-1 progress into Dean, goal, or priority progress.
- Org or team mapping (ecosystems, verticals); owners are individuals only.
- Migration to Microsoft Lists, Dataverse, or Power BI (separate later change).
- Mobile-optimized layouts beyond basic responsiveness.

## Capabilities

### New Capabilities
- `initiative-data`: Goals, priorities, people, initiatives, tags, links, and the rules that keep them consistent.
- `strategy-navigation`: Home screen and the goal and priority list screens.
- `initiative-card`: Initiative detail view with upward and downward connections.
- `person-card`: Everything one person owns, with stale flags.
- `progress-updates`: Self-reported percent, status, and note kept as a running diary.
- `admin-editing`: In-app fixes to descriptions, tags, links, and initiatives, with an audit trail.
- `meeting-view`: Weekly agenda page of changes, risks, and stale items.
- `shared-access`: Passcode gate, person selection, persistence, and backups.
- `data-intake`: Excel template, validated import, and data-quality checks.

### Modified Capabilities

## Impact

- New code: `app/` (routes, templates, static), `scripts/` (template generator, importer, backup), `tests/`.
- Schema additions in `db/schema.sql`: `People.IsAdmin`, `ProgressUpdates.CreatedAt`, `AuditLog`, `vw_RecentUpdates`.
- Python dependencies: fastapi, uvicorn, jinja2, python-multipart, itsdangerous, openpyxl, pytest, httpx.
- Runs locally for development and on Kevin's Hetzner VPS for live use (Docker Compose, HTTPS). New `Dockerfile`, `compose.yaml`, `deploy/` scripts. No changes to any Georgia Tech production system.
