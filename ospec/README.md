# CLL Initiative Dashboard (prototype)

Spec-driven with OpenSpec. The change to build is `add-initiative-dashboard-prototype`.

## Start in Claude Code

    npm install -g @fission-ai/openspec@latest
    openspec init --tools claude      # keeps the existing openspec/ files; adds /opsx commands
    openspec validate add-initiative-dashboard-prototype --strict
    python3 db/build_db.py            # sample database

Then in Claude Code: `/opsx:apply add-initiative-dashboard-prototype`
When done and verified: `/opsx:archive add-initiative-dashboard-prototype`
