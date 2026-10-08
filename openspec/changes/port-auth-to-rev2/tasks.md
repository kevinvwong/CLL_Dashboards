# Tasks: port-auth-to-rev2

## 1. Schema

- [x] 1.1 `db/mssql/010_auth.sql`: add `person.clerk_user_id` (nullable) + filtered unique index (`WHERE clerk_user_id IS NOT NULL`). No credential column (see proposal decision).
- [x] 1.2 Register `010` in `apply.py`; apply to live `cllrev2`.
- [x] 1.3 Record in `DEVIATIONS.md` (additions, same category as 008/009).

## 2. Auth ports (app/port.py)

- [x] 2.1 `auth_person(person_id)` â€” the `current_person` lookup / `person_exists` read (active, app key shape).
- [x] 2.2 `auth_active_people()`.
- [x] 2.3 `auth_get_initiative(mi_id)`.
- [x] 2.4 `auth_roles_of(person_id)` â€” `person_role` + `role`.
- [x] 2.5 `auth_person_by_clerk_id(clerk_user_id)`; `auth_link_person_to_clerk(person_id, clerk_user_id)`.
- [x] 2.6 PIN refusal under mssql: `person_credential`/`set_person_pin`/`verify_person_pin` raise a clear error naming the stopgap as local-only.

## 3. Wire auth.py

- [x] 3.1 Route the reads through port per engine; keep the sqlite bodies.
- [x] 3.2 `_role_ids`, `roles_of`, `has_role`, `is_admin`, `is_executive_sponsor`, `is_data_owner`, `is_operator`, `has_capability` resolve from the store in use (no per-engine branch in the guards themselves).
- [x] 3.3 Clerk link read/write via port; PIN refused on mssql.
- [x] 3.4 `person_exists` and the whoami path work on mssql.

## 4. Parity + gate

- [x] 4.1 Parity tests: `active_people`, `person_exists`, `roles_of`, `person_by_clerk_id` (empty on seed), each agreeing across stores.
- [x] 4.2 A test asserts the PIN stopgap raises under mssql (the refusal, not a silent pass).
- [x] 4.3 sqlite suite green (role/auth tests included).
- [x] 4.4 `openspec validate --strict`; regenerate PROGRESS_LOG; commit.
- [x] 4.5 Update DEPLOY.md / the earlier notes: the "one env var" claim is now true for authenticated requests too.
