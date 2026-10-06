# CLL Initiative Dashboard (prototype)

Spec-driven with OpenSpec. The change to build is `add-initiative-dashboard-prototype`.

## Run it locally

```powershell
cd ospec
python -m pip install -r openspec/changes/add-initiative-dashboard-prototype/requirements.txt
python db/build_db.py                       # writes ospec/cll_initiatives.db

cd openspec/changes/add-initiative-dashboard-prototype
python -m uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000> and sign in with the passcode in `.env`.

**The passcode lives in `.env` in the app folder, which is gitignored.** Create it
from `.env.example` if it is missing. `APP_PASSCODE`, `APP_SECRET`, `APP_ENV`, and
`DB_PATH` all come from there; nothing else needs setting.

**Start from the app folder, or set `DB_PATH` absolutely.** `Config.DB_PATH`
defaults to `./cll_initiatives.db`, resolved against the working directory. A
different working directory therefore points at a *different* file, and the app
folder already contains a stray empty one — the same one that once got packaged
into a deploy archive. The committed `.env` uses an absolute path so this cannot
happen; a shell that does not load `.env` will not.

Sample data only. The live service has its own settings in App Service; see
`docs/DEPLOY.md` for the deploy and the F1 stop-request quota trap.

## Start in Claude Code

    npm install -g @fission-ai/openspec@latest
    openspec init --tools claude      # keeps the existing openspec/ files; adds /opsx commands
    openspec validate add-initiative-dashboard-prototype --strict
    python3 db/build_db.py            # sample database

Then in Claude Code: `/opsx:apply add-initiative-dashboard-prototype`
When done and verified: `/opsx:archive add-initiative-dashboard-prototype`

