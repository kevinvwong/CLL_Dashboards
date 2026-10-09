#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Host diagnostic: what is this machine actually running, and can it reach its
# database?
#
# READ-ONLY. It inspects, it does not repair. Nothing here writes, restarts,
# stops, pulls, builds, or redeploys. Every database statement is a SELECT or a
# PRAGMA read.
#
# Purpose: answer, for a deployment nobody has shell history for -
#   * which commit is the container actually serving?
#   * is the database reachable, and what is IN it?
#   * is the database a single-file bind mount (which constrains SQLite)?
#   * what config is the app actually running with?
#
# Usage:  bash scripts/diagnose_host.sh
# Then paste the whole output back. Redact nothing by hand; secrets are
# redacted here.
# ---------------------------------------------------------------------------

set -u

CONTAINER="${CONTAINER:-}"
DB_PATH_IN_CONTAINER="${DB_PATH_IN_CONTAINER:-}"

say()  { printf '\n=== %s ===\n' "$1"; }
note() { printf '  %s\n' "$1"; }
warn() { printf '  !! %s\n' "$1"; }

have() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
say "host"
note "host      : $(hostname 2>/dev/null || echo '?')"
note "kernel    : $(uname -sr 2>/dev/null || echo '?')"
note "time (UTC): $(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo '?')"
note "script    : read-only diagnostic; repairs nothing"

# ---------------------------------------------------------------------------
say "containers"
if ! have docker; then
  warn "docker not on PATH - is this host running the app in Docker at all?"
  echo
  echo "If the app runs directly (systemd/supervisor), check:"
  echo "  systemctl status <service> ; journalctl -u <service> -n 100 --no-pager"
  exit 0
fi

docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}' 2>/dev/null || warn "docker ps failed"

if [ -z "$CONTAINER" ]; then
  # Prefer a container that looks like the app; fall back to the newest.
  CONTAINER="$(docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.CreatedAt}}' 2>/dev/null \
    | grep -iE 'cll|dashboard|app' | head -1 | cut -f1)"
fi
if [ -z "$CONTAINER" ]; then
  CONTAINER="$(docker ps -a --format '{{.Names}}\t{{.CreatedAt}}' 2>/dev/null | sort -k2 -r | head -1 | cut -f1)"
fi

if [ -z "$CONTAINER" ]; then
  warn "no container found; set CONTAINER=<name> and re-run"
  exit 0
fi
note ""
note "inspecting container: $CONTAINER"

RUNNING="$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo '?')"
RESTARTS="$(docker inspect -f '{{.RestartCount}}' "$CONTAINER" 2>/dev/null || echo '?')"
IMAGE="$(docker inspect -f '{{.Config.Image}}' "$CONTAINER" 2>/dev/null || echo '?')"
CREATED="$(docker inspect -f '{{.Created}}' "$CONTAINER" 2>/dev/null || echo '?')"
STARTED="$(docker inspect -f '{{.State.StartedAt}}' "$CONTAINER" 2>/dev/null || echo '?')"
USER="$(docker inspect -f '{{.Config.User}}' "$CONTAINER" 2>/dev/null || echo '?')"

note "running   : $RUNNING   restarts: $RESTARTS"
note "image     : $IMAGE"
note "created   : $CREATED"
note "started   : $STARTED"
note "run as    : ${USER:-<image default>}"

if [ "$RUNNING" != "true" ]; then
  warn "container is NOT running - that alone explains a 500. Recent logs:"
  docker logs --tail 60 "$CONTAINER" 2>&1 | sed 's/^/    /'
fi

# ---------------------------------------------------------------------------
say "which code is it serving?"
# The fingerprint that matters: does the running app have the Rev2/Azure SQL
# seam (MSSQL_* in config.py, and app/port.py)? If both are absent, this host
# predates the store port regardless of what git says is on main.
if [ "$RUNNING" = "true" ]; then
  for f in /app/app/config.py /app/app/port.py /app/app/db.py; do
    if docker exec "$CONTAINER" test -f "$f" 2>/dev/null; then
      note "present: $f"
    else
      note "absent : $f"
    fi
  done
  # grep -c prints 0 AND exits 1 when there are no matches, so `|| echo 0`
  # would append a second line and break the numeric test. Take the first line.
  CNT="$(docker exec "$CONTAINER" sh -c 'grep -c MSSQL_SERVER /app/app/config.py 2>/dev/null || true' 2>/dev/null | tr -d '\r' | head -1)"
  CNT="${CNT:-0}"
  case "$CNT" in ''|*[!0-9]*) CNT=0 ;; esac
  note "MSSQL_SERVER references in config.py : $CNT"
  if [ "$CNT" -gt 0 ]; then
    note "=> this build HAS the Rev2/Azure SQL store seam"
  else
    note "=> this build PREDATES the Rev2 store seam (DB_PROVIDER is sqlite-only here)"
  fi
  if docker exec "$CONTAINER" test -f /app/app/port.py 2>/dev/null; then
    note "app/port.py exists => store-port module present"
  else
    note "app/port.py MISSING => store-port module absent"
  fi
else
  warn "container not running; cannot fingerprint the code inside it"
fi

# ---------------------------------------------------------------------------
say "mounts"
# A single-FILE bind mount of a SQLite database is the configuration that makes
# SQLite's -wal/-shm sidecar files a problem. A DIRECTORY mount is fine.
docker inspect -f '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}} rw={{.RW}}{{"\n"}}{{end}}' \
  "$CONTAINER" 2>/dev/null | sed 's/^/  /' || warn "could not read mounts"

# ---------------------------------------------------------------------------
say "effective config (secrets redacted)"
if [ "$RUNNING" = "true" ]; then
  docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER" 2>/dev/null \
    | grep -Ei '^(DB_|AUTH_|APP_ENV|DEPLOY_MARKER|GIT_COMMIT|DOCS_PATH|PORT|CLERK)' \
    | sed -E 's/^([^=]*(SECRET|KEY|PASSWORD|TOKEN|PASSCODE)[^=]*)=.*/\1=<redacted>/I' \
    | sed 's/^/  /'
else
  note "(container not running)"
fi

# ---------------------------------------------------------------------------
say "database"
if [ "$RUNNING" != "true" ]; then
  warn "container not running; skipping the database probe"
else
  if [ -z "$DB_PATH_IN_CONTAINER" ]; then
    DB_PATH_IN_CONTAINER="$(docker exec "$CONTAINER" sh -c 'printf %s "${DB_PATH:-./cll_initiatives.db}"' 2>/dev/null | tr -d '\r\n')"
  fi
  note "DB_PATH (in container): ${DB_PATH_IN_CONTAINER:-<unset>}"

  docker exec -i "$CONTAINER" sh -c 'ls -ln "$(dirname "$1")" 2>&1; echo; id' \
    sh "$DB_PATH_IN_CONTAINER" 2>/dev/null | sed 's/^/  /'

  # The probe is piped in on stdin, so there is no nested quoting to get wrong.
  docker exec -i "$CONTAINER" python - "$DB_PATH_IN_CONTAINER" <<'PYEOF' 2>&1 | sed 's/^/  /'
import os, sqlite3, sys
p = sys.argv[1] if len(sys.argv) > 1 else ""
if not p:
    p = os.environ.get("DB_PATH", "./cll_initiatives.db")
if not os.path.exists(p):
    print("FILE MISSING:", p)
    raise SystemExit(0)
print("path      :", p)
print("size      :", os.path.getsize(p), "bytes")
print("readable  :", os.access(p, os.R_OK))
print("writable  :", os.access(p, os.W_OK))
try:
    with open(p, "rb") as fh:
        print("magic     :", fh.read(15))
except Exception as e:
    print("READ FAILED:", type(e).__name__, e)
try:
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    print("journal   :", c.execute("PRAGMA journal_mode").fetchone()[0])
    t = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("tables    :", len(t))
    print("integrity :", c.execute("PRAGMA integrity_check").fetchone()[0])
    for name in ("TeamInitiatives", "TeamInitiativeUpdates", "AuditLog",
                 "Goals", "Priorities", "DeanInitiatives", "Milestones",
                 "People", "TeamInitiativeDeanLinks", "AppMeta"):
        if name in t:
            n = c.execute("SELECT COUNT(*) FROM %s" % name).fetchone()[0]
            print("  %-26s %d rows" % (name, n))
    c.close()
except Exception as e:
    print("OPEN/QUERY FAILED:", type(e).__name__, str(e)[:300])
PYEOF
fi

# ---------------------------------------------------------------------------
say "recent container logs (tail)"
if [ "$RUNNING" = "true" ] || [ "$RUNNING" = "false" ]; then
  docker logs --tail 40 "$CONTAINER" 2>&1 | tail -40 | sed 's/^/  /'
else
  warn "no container"
fi

# ---------------------------------------------------------------------------
say "backups on this host"
for d in /var/lib/platform/backups/cll-dashboards /var/backups /srv/backups ./backups; do
  if [ -d "$d" ]; then
    note "$d"
    ls -ln "$d" 2>/dev/null | tail -12 | sed 's/^/    /'
  fi
done

say "done"
note "This script changed nothing. Paste the full output back for analysis."