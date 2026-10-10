# Tasks: specify-passcode-person-resolution-under-mssql

## 1. Verify the behaviour already holds

- [x] 1.1 (verify) on the live store, resolve a passcode-authenticated person under `DB_PROVIDER=mssql` and confirm the same key shape sqlite returns: call `port.auth_person` with `provider="mssql"` and with `provider="sqlite"` for the same `PersonID` and compare `PersonID`/`Name`/`Title`. If they disagree, stop and report Ã¢â‚¬â€ the scenario would be publishing behaviour that does not exist.
- [x] 1.2 (verify) confirm no sqlite fallback exists on the mssql branch of `current_person` / `port.auth_person` (read the code; the Clerk and local branches both resolve through the store seam).
- [x] 1.3 (verify) confirm `AUTH_PROVIDER=local` is what deployed environments run, per `docs/ops/DEPLOY.md`'s identity section, so the scenario's GIVEN names the real configuration.

## 2. Sync

- [x] 2.1 Apply the delta to `openspec/specs/rev2-auth/spec.md`: MODIFIED *"authentication resolves people and roles on the selected store"* carrying its three existing scenarios plus the new *"a passcode-selected person resolves under mssql"*. (verify: `openspec validate --specs` passes; `rev2-auth` keeps 3 requirements and carries no delta operation headers.)
- [x] 2.2 Archive the change, which merges the delta into the main spec.

## 3. Gate

- [x] 3.1 `python -m pytest -q` Ã¢â‚¬â€ exit 0. No test asserts this scenario, so this is a regression guard only.
- [x] 3.2 Regenerate `docs/ops/PROGRESS_LOG.md` (`--check` clean) and commit it with the change.
- [x] 3.3 `openspec validate --all --strict` and `--specs` pass.
