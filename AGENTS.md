# CLL Initiative Dashboard — agent guide

Repo-wide instructions for coding agents. Domain vocabulary lives in `CONTEXT.md`;
this file records where the engineering skills keep their configuration.

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues in `kevinvwong/CLL_Dashboards`, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Progress log

`docs/ops/PROGRESS_LOG.md` is **generated** — never edit it by hand. It is a
plain-English, day-by-day record for a non-technical reader, built from git
history by `scripts/build_progress_log.py`. After committing work, refresh it and
commit it with the change:

```
python scripts/build_progress_log.py            # regenerate
python scripts/build_progress_log.py --check    # assert it is current (CI)
```

A test (`tests/test_progress_log.py`) fails if the committed log is stale, so a
forgotten regeneration is caught rather than shipping an out-of-date record.
