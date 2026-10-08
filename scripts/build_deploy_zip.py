"""Build the deployment archive for the live App Service.

    python scripts/build_deploy_zip.py [output.zip]

Why this exists in the repo rather than in a shell history:

  - PowerShell's `Compress-Archive` writes BACKSLASH separators into the zip, and
    Linux Kudu/rsync cannot stat them. The deploy then fails with a bare
    `Kudu Status: 400` whose real cause is one line deep:
        rsync: failed to stat ".../app\\main.py": Invalid argument (22)
    So the zip is built here with an explicit '/'.

  - `az webapp deploy --type zip` REPLACES /home/site/wwwroot, and nothing in the
    application recreates the SQLite database at startup. A zip that omits it
    takes the live site down with "database unreachable". It has happened once.
    This script refuses to produce an archive without it.

See docs/DEPLOY.md for the procedure that uses this.
"""

import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.dirname(HERE)  # the repo root
# The application package. App Service serves it as the `app` package, so the
# walk below prefixes every entry with "app/" - the site imports `app.main:app`.
APP = os.path.join(SPEC, "app")
APP_PREFIX = "app"

DEFAULT_OUT = os.path.join(SPEC, "deploy.zip")

# Bytecode and test scaffolding: not needed at runtime, and shipping tests slows
# the build for no benefit.
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "tests"}
SKIP_EXT = {".pyc", ".pyo"}

# Secrets, never shipped. The walk visits the application folder, and a local
# `.env` sits there (it holds APP_PASSCODE, APP_SECRET and DB_PATH). It was
# packaged into the archive until 2026-10-06; `.env.example` is the documented
# shape and is fine to ship, but any other `.env*` is a credential file.
SKIP_NAMES = {".env", ".env.local", ".env.production", ".env.live", ".env.development"}

# A shipped file whose name matches this fails the build, so a future secret file
# with a new name is caught rather than packaged. `.env.example` is the documented
# shape and is explicitly allowed (it is the one `.env*` name that holds no secret).
SECRET_NAME_RE = re.compile(r"(^|/)\.env(\.[a-z0-9]+)?$|\.(pem|key|pfx|p12)$",
                            re.IGNORECASE)
ALLOWED_NAMES = {".env.example"}

# The database and the files needed to recreate it. App Service serves
# DB_PATH=./cll_initiatives.db relative to wwwroot, so the db ships at the archive
# root and the schema and seed beside it under db/.
#
# seed_team_layer.sql is REQUIRED and was missing until 2026-10-06: the schema
# gained Teams/SourceAreas/TeamKPIs, but only seed_sample.sql shipped, so a
# rebuild from the archive produced the tables with no rows. The deployed db
# file itself was fine, which is exactly why this was invisible - the rebuild
# path, not the shipped data, was broken.
REQUIRED = [
    (os.path.join(SPEC, "cll_initiatives.db"), "cll_initiatives.db"),
    (os.path.join(SPEC, "db", "schema.sql"), "db/schema.sql"),
    (os.path.join(SPEC, "db", "seed_sample.sql"), "db/seed_sample.sql"),
    (os.path.join(SPEC, "db", "seed_team_layer.sql"), "db/seed_team_layer.sql"),
    # The register seed (2026-10-07) is REQUIRED: build_db.py loads it after the
    # others, and it is the only source of the Dean layer, the owners, and the
    # four team reassignments. Omitting it leaves the rebuild path broken — the
    # same class of defect seed_team_layer.sql had until 2026-10-06.
    (os.path.join(SPEC, "db", "seed_register.sql"), "db/seed_register.sql"),
    (os.path.join(SPEC, "db", "seed_canon_links.sql"), "db/seed_canon_links.sql"),
    (os.path.join(SPEC, "requirements.txt"), "requirements.txt"),
    # `.env.example` is documentation, not a secret: it ships so a deployed copy
    # has the shape of the settings to set. The real `.env` never does.
    (os.path.join(SPEC, ".env.example"), ".env.example"),
]

# Asserted present after building. A missing one means a broken deploy, so the
# script fails loudly rather than producing an archive that takes the site down.
#: The in-app guide reads its markdown from DOCS_PATH. These files ship so the
#: guide renders live. (source_path, arcname) - the whole docs tree is small and
#: self-consistent, so it ships whole rather than by a fragile hand-list.
DOCS = os.path.join(SPEC, "docs")

# Verified present after building.
MUST_CONTAIN = ["app/main.py", "app/templates/base.html", "requirements.txt",
                "cll_initiatives.db", "docs/guide.yaml"]


def build(out_path: str = DEFAULT_OUT) -> str:
    if not os.path.isdir(APP):
        raise SystemExit("application directory not found: %s" % APP)

    # REQUIRED is authoritative for these arcnames. The walk below also visits the
    # application folder, and a cwd-relative default database can be sitting there
    # (Config.DB_PATH defaults to "./cll_initiatives.db", so anything that connects
    # without an explicit path from that directory leaves an EMPTY one behind).
    # Writing both produces a DUPLICATE entry, and which one wins on extraction is
    # order-dependent - so the archive could ship the empty database and take the
    # site down with "database unreachable". Skip the walk's copy and let REQUIRED
    # win.
    reserved = {arc for _, arc in REQUIRED}

    added = []
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        # The walk visits the `app` package and prefixes each entry with `app/`,
        # so the site's `app.main:app` import resolves. `.env.example` and
        # `requirements.txt` are siblings of `app/`, not inside it, so they come
        # from REQUIRED below rather than this walk.
        for root, dirs, files in os.walk(APP):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                if os.path.splitext(fn)[1] in SKIP_EXT:
                    continue
                if fn in SKIP_NAMES:
                    continue
                full = os.path.join(root, fn)
                arc = os.path.join(APP_PREFIX,
                                   os.path.relpath(full, APP)).replace(os.sep, "/")
                if arc in reserved:
                    continue
                if SECRET_NAME_RE.search(arc) and arc not in ALLOWED_NAMES:
                    continue
                z.write(full, arc)
                added.append(arc)

        for src, arc in REQUIRED:
            if not os.path.exists(src):
                raise SystemExit("required file missing, refusing to build: %s" % src)
            z.write(src, arc)
            added.append(arc)

        # The docs the in-app guide renders (2026-10-07). Shipped whole: the guide
        # reads markdown from DOCS_PATH, and a missing chapter is worse than a
        # slightly larger archive. Skips the repo's own agent/ops scratch only if a
        # secret-shaped name appears (none do).
        if os.path.isdir(DOCS):
            for root, dirs, files in os.walk(DOCS):
                dirs[:] = [d for d in dirs if d not in {"assets"}]
                for fn in files:
                    if os.path.splitext(fn)[1].lower() not in {".md", ".yaml", ".yml"}:
                        continue
                    full = os.path.join(root, fn)
                    arc = os.path.join("docs",
                                       os.path.relpath(full, DOCS)).replace(os.sep, "/")
                    if SECRET_NAME_RE.search(arc) and arc not in ALLOWED_NAMES:
                        continue
                    z.write(full, arc)
                    added.append(arc)

    # Verify, rather than trust the loop above.
    with zipfile.ZipFile(out_path) as z:
        names = z.namelist()

    # A credential file in a deploy archive is a leak. `.env.example` is the
    # documented shape and holds no secret; anything else that looks like one is a
    # failure, not a warning - this archive was shipping a local `.env` until
    # 2026-10-06.
    leaked = sorted(n for n in names
                    if SECRET_NAME_RE.search(n) and n not in ALLOWED_NAMES)
    if leaked:
        raise SystemExit(
            "archive would ship a credential file, refusing to build: %s" % leaked)

    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise SystemExit(
            "archive contains duplicate entries, extraction order decides the "
            "winner and the deployed database could be the empty one: %s"
            % duplicates)

    backslashes = [n for n in names if "\\" in n]
    if backslashes:
        raise SystemExit(
            "archive contains backslash separators, Linux Kudu cannot stat them: %s"
            % backslashes[:3])

    missing = [n for n in MUST_CONTAIN if n not in names]
    if missing:
        raise SystemExit("archive is missing required entries: %s" % missing)

    return out_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    path = build(out)
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    print("Built %s" % path)
    print("  entries     : %d" % len(names))
    print("  backslashes : %d (must be 0)" % sum(1 for n in names if "\\" in n))
    print("  templates   : %d" % sum(1 for n in names if n.startswith("app/templates/")))
    print("  size        : %.1f KB" % (os.path.getsize(path) / 1024))
