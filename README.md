# CLL Initiative Dashboard

The dashboard service for the Dean's Wednesday leadership meeting. Domain
vocabulary lives in `CONTEXT.md`; the engineering-skills configuration is in
`docs/agents/`.

## Run it locally

The quickest way, from anywhere:

```bat
run-dashboard.cmd            :: port 8000
run-dashboard.cmd 8010       :: a different port
run-dashboard.cmd 8000 --reload
```

It resolves its own location, so it works from any working directory, and picks
a Python that has the dependencies.

By hand, from the repo root:

```powershell
python -m pip install -r requirements.txt
python db/build_db.py                       # writes ./cll_initiatives.db
python -m uvicorn app.main:app --reload     # serves the app package
```

Then open <http://127.0.0.1:8000> and sign in with the passcode in `.env`.

**The passcode lives in `.env`, which is gitignored.** Create it from
`.env.example` if it is missing. `APP_PASSCODE`, `APP_SECRET`, `APP_ENV`, and
`DB_PATH` all come from there; nothing else needs setting.

**Run from the repo root, or set `DB_PATH` absolutely.** `Config.DB_PATH`
defaults to `./cll_initiatives.db`, resolved against the working directory, so a
different working directory points at a *different* file. The committed `.env`
uses an absolute path so this cannot happen; a shell that does not load `.env`
will not.

## Test

```powershell
python -m pytest
```

Configuration is in `pyproject.toml` (`testpaths`, `pythonpath`), so no path
setup is needed running from the root.

Sample data only. The live service has its own settings in App Service; see
`docs/ops/DEPLOY.md` for the deploy and the F1 stop-request quota trap.

## Layout

```
.
├── app/          the FastAPI application package (app.main:app)
├── tests/        the test suite (pytest)
├── db/           schema, seeds, the sample database, and the builders
├── scripts/      the deploy-archive builder and the oct16 generators
├── docs/
│   ├── agents/   issue tracker, triage labels, domain-doc rules
│   ├── specs/    the design specs
│   ├── ops/      DEPLOY.md, LAUNCH_RECORD.md
│   └── source/   AUTHORITATIVE_SOURCE.md, DEAN_DECISIONS.md
├── source/       external source packages (gitignored), read in place
├── pyproject.toml
└── requirements.txt
```
