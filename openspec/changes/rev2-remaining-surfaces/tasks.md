# Tasks: rev2-remaining-surfaces

## 1. Port the six surfaces in app/port.py and wire them in queries.py

- [x] 1.1 `initiative_signals` â†’ `vw_initiative_summary` + Reporting Owner + `vw_latest_update` (derived latest). Wire in.
- [x] 1.2 `relationships_for` â†’ `initiative_relationship` (D-1 `Supports`/`Contributes To` â†’ Dean), keyed by `MI-###`. Wire in.
- [x] 1.3 `dean_initiatives` â†’ `initiative(level='Dean')` + priority edge + D-1 roll-up from `initiative_relationship`. Wire in; keep the FY26/FY27 order and the `fiscal_year`/`priority_*` keys the template uses.
- [x] 1.4 `team_initiative_dean_links` â†’ `initiative_relationship` joined to the Dean row. Wire in.
- [x] 1.5 `data_checks` â†’ `initiative` NOT EXISTS `initiative_goal` / `initiative_priority`. Wire in.
- [x] 1.6 `recent_changes` â†’ `audit_log` JOIN `person` (newest first). Wire in.

## 2. Parity coverage

- [x] 2.1 Extend `tests/test_store_parity.py` to cover all six surfaces (each returns equal results on both stores).

## 3. Gate

- [x] 3.1 sqlite suite green; parity suite green.
- [x] 3.2 `openspec validate --strict` passes.
- [x] 3.3 Regenerate `docs/ops/PROGRESS_LOG.md`; `git checkout -- cll_initiatives.db` if dirtied.
- [x] 3.4 Record in `adopt-rev2-store` / DEPLOY that the read surface is now complete end-to-end under mssql (the earlier completion note underclaimed while these six were unported).
