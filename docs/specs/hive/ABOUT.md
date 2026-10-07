# Hive reference copy

A snapshot of the Hive design system, copied here so the dashboard restyle has a
source of truth inside the repo. Snapshot: 2026-10-06.

- `README.md` — the brand book: principles, GT lineage table, color, type, shape, content.
- `dashboards.md`, `data-visualization.md`, `presentations-and-documents.md` — the usage sections.
- `tokens.json` — every token with Day and Night values and a usage note. Values written `{name}` are aliases of another token.
- `tokens.css` — the same tokens compiled to CSS custom properties (reference only; font URLs here are relative to this folder, the app uses `/static/fonts/`).
- `components/bundle.css` — Hive's own component styles (`hv-*` classes), a visual reference for buttons, badges, tables, cards and the app bar. Do not ship it; map its look onto the app's existing classes.
- `fonts/` — the ten self-hosted woff2 files and their SIL OFL licenses. Copy to `app/static/fonts/`.
- `assets/logos/` — the official GT web logos (four lockups, five colorways), unaltered, with usage rules. Copy `GTLogo_GoldWhite.svg` to `app/static/brand/`.

The live Hive system, with component previews, is maintained by Kevin Wong. When Hive changes, update this copy and the brief together.
