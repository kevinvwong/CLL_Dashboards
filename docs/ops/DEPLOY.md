# Deploy runbook

How to deploy the live service, verify it, and roll it back.

**Service:** `clldashproto2kwong27.azurewebsites.net`
**Resource group:** `rg-cll-dash-proto` (region `northcentralus`)

Written because the deploy path existed only as shell history, its exit code
reports failure while succeeding, and a bad archive takes the site down.

---

## Environment policy (set 2026-10-07)

**Local is dev. Azure is production. Do NOT deploy to Azure until the user
declares a checkpoint.**

- **Develop and test against the local server** (`run-dashboard.cmd`,
  `http://127.0.0.1:8000`). The suite runs locally. The database builds
  locally. Nothing goes to Azure by default.
- **A deploy is a promotion, not a step in the loop.** It happens only when the
  user explicitly declares a checkpoint — a point they have decided is worth
  putting in front of people. Until then, "it works locally" is the done state.
- **No agent should deploy on its own initiative**, including to "verify a fix
  landed on the live site". Verify locally instead.

**Production state at the time of this policy:** marker
`labels-20261007T123612Z` (the `/dean-initiatives` + "Goal N" + status-glyph
round). Production is therefore AHEAD of nothing and BEHIND any local work done
after `f24cc5d` until the next declared checkpoint.

**Latest production checkpoint:** marker `shell-guide-20261007T203634Z` at commit
`198da95` — the persistent left-rail shell (rail / icon-rail / bottom tab bar)
and the in-app `/guide` documentation set. The deploy also sets
`DOCS_PATH=./docs` so the guide renders from the shipped docs. Verified live
2026-10-07 20:36 UTC: stamp reads `198da95 · deployed 2026-10-07 20:36 UTC`, the
rail and guide render, a non-admin sees user chapters only, and the technical
chapter is refused.

**Previous checkpoint:** marker `enhance-20261007T195252Z` at commit `bae40b7` — the Milestones model, the intake, the DB-backed Outcomes page, goal
and team identity, the enhancements and motion, and the auth stopgap (PIN +
local roles + change-log fields). Verified live 2026-10-07 19:52 UTC: the header
stamp reads `bae40b7 · deployed 2026-10-07 19:52 UTC`, and the gate and the new
visuals were walked.

### Two runbook notes that cost time this session

- **`az webapp deploy` blocks the shell while it polls** — but the deploy
  succeeds. Run it as a background process and poll `/healthz` for the marker,
  rather than waiting on the command (see step 4).
- **Stop the local dev server before running the test suite.** A running
  `uvicorn` holds `cll_initiatives.db`, so `test_build_is_reproducible` fails
  spuriously — the build cannot replace a file another process has open.

---

## Prerequisites

| What | Where |
|---|---|
| `az` wrapper | `C:\Users\kwong318\aztools\azure-cli\python.exe` |
| Python | `C:\Users\kwong318\AppData\Local\Programs\Python\Python312\python.exe` |
| Passcode for the live site | `%TEMP%\cll-creds2.txt`, key `APP_PASSCODE` |
| App Service settings | `DEPLOY_MARKER`, `APP_ENV=live`, `DB_PATH=./cll_initiatives.db`, `DOCS_PATH=./docs`, `APP_PASSCODE`, `APP_SECRET` |
| Clerk (only when `AUTH_PROVIDER=clerk`) | `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_AUTHORIZED_PARTY` (the live origin) |

**Never commit a credential.** The passcode lives in `%TEMP%` and is passed to
`az` through the shell; it does not appear in this document or in any file under
version control.

**Use the bundled interpreter, not `az.cmd`.** On Windows `az` is a `.cmd` shim,
and `cmd.exe` re-parses its arguments — so `--runtime "PYTHON|3.12"` becomes a pipe
and values containing `%` are expanded. Call the interpreter directly:

```
& "C:\Users\kwong318\aztools\azure-cli\python.exe" -IBm azure.cli <command>
```

---

## 1. Build the archive

```
cd C:\Users\kwong318\GitHub\CLL_Dashboards
python scripts\build_deploy_zip.py
```

This writes `deploy.zip`. It refuses to build if a required file is missing,
and it prints the entry count and a backslash count that **must be 0**.

**Why the archive's contents matter.** `az webapp deploy --type zip` *replaces*
`/home/site/wwwroot`, and nothing in the application recreates the SQLite database
at startup. An archive omitting `cll_initiatives.db` therefore deletes the only
copy and the site fails `/healthz` with `database unreachable`. This has happened
once. `build_deploy_zip.py` asserts the file is present.

**Why forward slashes matter.** PowerShell's `Compress-Archive` writes backslash
separators, and Linux Kudu cannot stat them. The deploy fails with a bare
`Kudu Status: 400` whose real cause is buried:
`rsync: failed to stat ".../app\main.py": Invalid argument (22)`. Always build
with the script, never with `Compress-Archive`.

What the archive contains, and why:

| Entry | Why |
|---|---|
| `app/**` | the application |
| `requirements.txt` | Oryx installs from it when `SCM_DO_BUILD_DURING_DEPLOYMENT=true` |
| `cll_initiatives.db` | the live database; **omitting it takes the site down** |
| `db/schema.sql`, `db/seed_sample.sql` | so the database can be rebuilt in place |

Excluded: `__pycache__/`, `.pytest_cache/`, `tests/`, `*.pyc`, `.git/`.

---

## 2. Set the revision marker

The marker makes "is the code I just deployed the code being served?" answerable
over plain HTTP. Use a unique value per deploy. Also set `GIT_COMMIT` so the
**header stamp** can name the code the app is running (see below).

```powershell
$marker  = "launch-" + (Get-Date -Format "yyyyMMddTHHmmss") + "Z"
$commit  = git -C C:\Users\kwong318\GitHub\CLL_Dashboards rev-parse --short HEAD
& "C:\Users\kwong318\aztools\azure-cli\python.exe" -IBm azure.cli webapp config appsettings set `
    --name clldashproto2kwong27 --resource-group rg-cll-dash-proto `
    --settings "DEPLOY_MARKER=$marker" "GIT_COMMIT=$commit" --output none
```

Record `$marker`. Step 4 needs it.

### The header stamp

A discreet line at the bottom of the app bar shows the **last push (short
commit) and the deploy time** — e.g. `e1c55d4 · deployed 2026-10-07 16:10 UTC`.
The deploy time is read from the marker's `…T…Z` suffix, so `DEPLOY_MARKER`
alone is enough for the time; `GIT_COMMIT` adds the commit. Both are unset in
local dev, and the stamp hides itself rather than showing a fake revision
(`tests/test_build_stamp.py`).

| Setting | Source | Shown as |
|---|---|---|
| `GIT_COMMIT` | `git rev-parse --short HEAD` | the short commit |
| `DEPLOY_MARKER` | `$marker` (suffix is the deploy time) | `deployed <time> UTC` |


---

## 3. Deploy

```powershell
& "C:\Users\kwong318\aztools\azure-cli\python.exe" -IBm azure.cli webapp deploy `
    --name clldashproto2kwong27 --resource-group rg-cll-dash-proto `
    --src-path "C:\Users\kwong318\GitHub\CLL_Dashboards\deploy.zip" `
    --type zip --output none
```

### The exit code is not the verdict

**`az webapp deploy` exits 1 while succeeding.** `az` writes warnings to stderr —
including the harmless note that it does not run build automation — and that is
enough for PowerShell to surface a non-zero status. A successful deploy looks like
this:

```
WARNING: Build successful
WARNING: Starting the site...
exit code 1
```

So: **capture the output and the exit code as an artefact, then go to step 4.**
Never report a deploy as failed, or as successful, on the exit code alone. Trusting
it in the failed direction wastes a deploy; trusting a zero in the succeeded
direction ships a broken revision.

---

## 4. Verify — this is what decides success

Poll `/healthz` until it reports **the marker you set in step 2**. That observation,
not the command's exit code, is the verdict.

```powershell
$expected = "<the marker from step 2>"
1..20 | ForEach-Object {
    Start-Sleep -Seconds 15
    $h = (Invoke-WebRequest "https://clldashproto2kwong27.azurewebsites.net/healthz" `
            -UseBasicParsing -TimeoutSec 30).Content
    "attempt $_ : $h"
    if ($h -match [regex]::Escape($expected)) { "LIVE"; break }
}
```

- Marker matches → the deploy succeeded. Continue.
- Polling exhausts without a match → the new revision is **not** serving. Treat as
  failed and roll back (below).

Then walk the gate:

| Path | Expected |
|---|---|
| `/healthz` | 200, `ok DEPLOY_MARKER=<marker>` |
| `/robots.txt` | 200, `User-agent: *` / `Disallow: /` |
| `/login` | 200 |
| `/` unauthenticated | 303 to `/login` |
| `/oct16` signed in as Bill | 200, six outcome cards |

A 503 from `/healthz` reading `database unreachable` means the archive omitted the
database. Rebuild with the script and redeploy.

**A 403 reading `This web app is stopped` is the F1 plan's quota, not your deploy.**
Observed 2026-10-06 while deploying groups 1–3. The Free (F1) plan enforces
`WP stop requests` — **15 per hour** — and every deploy, start, and idle shutdown
counts as one. Cross it and Azure stops the **whole shared plan**, so *both* apps on
`cll-dash-proto-plan` return 403 with an empty body and `state: QuotaExceeded`. The
deploy itself succeeded; it was the stop that exceeded the cap. Diagnose it, do not
redeploy:

```powershell
& "...azure-cli\python.exe" -IBm azure.cli webapp show `
    --name clldashproto2kwong27 --resource-group rg-cll-dash-proto `
    --query "{state:state, usageState:usageState}" -o json
# "state": "QuotaExceeded"  -> the plan is stopped, not the deploy
```

The counter resets hourly (`nextResetTime`). Space deploys out, or move to a paid
tier before a launch where several deploys land in one hour. **Do not** treat this as
a rollback trigger: rolling back is another stop request and deepens the problem.

**Do not try to `webapp start` your way out of it.** Measured 2026-10-06: a
`webapp start` is itself a stop request, so it raises the count *and pushes
`nextResetTime` out by another hour*. Two start attempts moved the reset from
`17:00Z` to `18:00Z` and the count from 16 to 34, so the plan stayed down longer than
if it had been left alone. The count is visible and so is the reset:

```powershell
& "...azure-cli\python.exe" -IBm azure.cli rest --method get --url `
  "https://management.azure.com/subscriptions/<sub>/resourceGroups/rg-cll-dash-proto/providers/Microsoft.Web/serverfarms/cll-dash-proto-plan/usages?api-version=2023-12-01"
# WP stop requests: <count> / 15, nextResetTime <t>
```

Wait for `nextResetTime` and do nothing until then. If a launch cannot afford an
hour of downtime, that is the argument for leaving the F1 tier, not for poking it.

---

## The October 16 data swap

The page's content lives in `app/oct16_data.py`, which is **generated**. Once real
owners exist, the swap is two commands, and the module is never hand-edited.

**Step 1 — see what the swap will do, without doing it.**

```powershell
cd C:\Users\kwong318\GitHub\CLL_Dashboards
python scripts\swap_oct16_data.py --owners owners.json --dry-run
```

This prints every difference — owners gained, statuses changed, milestones moved —
and **writes nothing**. The committed module is byte-identical afterwards; the
suite asserts this (`test_dry_run_writes_nothing`). Read the report before step 2.

**Step 2 — run it.** This backs the database up, then regenerates the module.

```powershell
python scripts\swap_oct16_data.py --owners owners.json
```

It prints the backup filename. **Record it**: that file is the data half of a
rollback (step 5b). Then deploy per steps 1–4 above.

**The marker clears itself.** The page's top line is derived from the module, not
from an app setting, so nothing else has to be changed at swap time. An owners
file that names nobody is refused as confirmation — it builds the illustrative
module instead of claiming `Partly confirmed — 0 of 6`. See the `confirmed-data`
spec for why the marker is derived rather than set.

**Owners file format.** `{ "P01": {"owner": "Some Person", "updated": "2026-10-13"} }`.
`"[owner withheld]"` means an owner exists but their name is not placed on this
service: it renders as a marked placeholder and is never counted as confirmed.

---

## 5. Rollback

Rollback has two halves. A revision-only rollback is **not** sufficient once data
has been swapped: reverting the code while leaving the new data produces a state
that never existed.

**5a. Restore the previous revision.** App Service keeps deployment history.

```powershell
& "...azure-cli\python.exe" -IBm azure.cli webapp log deployment list `
    --name clldashproto2kwong27 --resource-group rg-cll-dash-proto `
    --query "[0:5].{time:start_time,id:deployment_id,msg:message}" -o table
```

Redeploy the archive for the revision you want to return to, or use
`az webapp deployment source` / the portal's deployment history to redeploy it.
Then re-run step 4 with that revision's marker.

**5b. Restore the previous database**, if the launch included a data swap.

```powershell
cd C:\Users\kwong318\GitHub\CLL_Dashboards
python scripts\backup.py          # takes the current state first, in case
# restore backups\cll_<date>.db over cll_initiatives.db, then redeploy
```

The backup filename taken *before* the swap is recorded at the time of the swap.
Restoring without it means reconstructing data, which is why it is taken first.

**5c. Confirm.** Probe `/healthz` and walk the gate table above. Confirm the
figures match the pre-launch state — not merely that the service responds.

---

## Why the rollback is exercised before launch

A rollback first attempted during an incident is a rollback that does not work.
It was performed once against the live service and re-deployed forward; the note
below records when.

---

## Record of exercises

| Date | What | Result |
|---|---|---|
| 2026-10-07 | Archive build refuses a missing database (`1.1`) | Passed — exited 1 naming the file |
| 2026-10-07 | Rollback performed against live, then re-deployed forward (`1.4`) | Passed — see below |

### 1.4 — the rollback exercise, in full

Deliberately deployed the failure the runbook guards against, then recovered.

| Step | Observation |
|---|---|
| Built an archive with the database omitted | 50 entries, `cll_initiatives.db` absent |
| Deployed it, marker `rollback-test-20261006T113922Z` | Command **exited 1** |
| Polled `/healthz` | **503 `database unreachable`** on the first attempt — the failure is detectable within ~15s, not silent |
| Re-deployed the known-good archive, marker `rollback-restored-20261006T114056Z` | Command **exited 1** again |
| Polled `/healthz` | **200 `ok DEPLOY_MARKER=rollback-restored-...`** on the first attempt |
| Walked the gate | `/healthz` 200 · `/robots.txt` 200 · `/login` 200 · `/` 303 to `/login` · `/oct16` 200 · `/meeting` 200 · `/checks` 200 |

**What this proves:** the failure takes the site down, it is detected by the probe
rather than by the exit code, and the rollback restores service on the first poll.
**What it also proves:** the exit code was 1 on the *successful* deploy too — so it
carries no information either way, which is why step 4 is the verdict.

