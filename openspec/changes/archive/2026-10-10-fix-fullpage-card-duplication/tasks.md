# Tasks: fix-fullpage-card-duplication

## 1. Verify the duplication is systematic

- [x] 1.1 (verify) for all 29 active Team Initiatives, `initiative_card(...)["Description"]` equals `team_initiative_detail(...)["Description"]` Ã¢â‚¬â€ 0 mismatches expected. A mismatch means the two reads are not the same field and the description block must not be merged.
- [x] 1.2 (verify) for the same 29, the Dean "Contributes to" set from `initiative_card(...)["connections"]` (by `InitiativeName`) equals `team_initiative_dean_links(...)` (by `dean_title`) Ã¢â‚¬â€ 0 mismatches expected, and each `connections` row should carry the linkable `Code`.
- [x] 1.3 (verify) confirm no other template includes `_card_body.html` besides `card.html` (drawer) and `team_initiative.html` (full page), so the change cannot affect a third caller.

## 2. Fix

- [x] 2.1 `_card_body.html`: gate the `card-code` + `card-title` block on the same condition the close control already uses (`{% if modal is not defined or modal %}`). Do not gate `card-owner` Ã¢â‚¬â€ it has no counterpart in the page heading.
- [x] 2.2 `team_initiative.html`: move the `section-heading` (eyebrow, `h1`, source-target chip) **above** the card body so the `h1` leads the page.
- [x] 2.3 `team_initiative.html`: remove the duplicate `mi-description` paragraph and the duplicate `dean_links` "Contributes to" section, keeping the fragment's richer copy.
- [x] 2.4 Confirm the two existing assertions still pass unchanged Ã¢â‚¬â€ `test_cards.py`'s fragment-vs-full-page pair and `test_dean_layer.py`'s description/Dean-links test. If either needs editing, stop and report why rather than weakening it.

## 3. Regression test

- [x] 3.1 Add a test asserting each duplicated string appears **exactly once** on the full page for a representative initiative: the title, the code+level, the description, and one Dean name. Assert count, not presence Ã¢â‚¬â€ presence is what let the bug ship.
- [x] 3.2 Add a test asserting the `h1` renders **before** the card body's content in document order (e.g. `html.index('<h1') < html.index('card-body')`), so the inverted outline cannot return.

## 4. Gate

- [x] 4.1 (verify) start the local server, load `/team-initiatives/MI-001`, and confirm no duplicated header/title/description, one "Contributes to", and the `h1` at the top. Also load the drawer fragment (`HX-Request`) and confirm it still carries its own title and close control. Stop the server afterwards and restore `cll_initiatives.db` if the run dirtied it.
- [x] 4.2 `python -m pytest -q` Ã¢â‚¬â€ exit 0.
- [x] 4.3 Regenerate `docs/ops/PROGRESS_LOG.md` (`--check` clean) and commit it with the change.
