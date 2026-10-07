# Authentication is a swappable adapter behind one Principal seam

**Status:** accepted (2026-10-07)

Today identity is a **self-asserted person picker** behind a shared passcode
(`app/auth.py`). The escalation vector is the picker, not the passcode:
`POST /whoami` lets anyone holding the passcode become any `Person`, including
the admin (`app/main.py:274–283`). The signed cookie and per-request DB role
reads are otherwise sound, so replacing self-assertion is the whole job.

Entra app registration is blocked — the host is a personal `Azure for Students`
subscription whose tenant is **outside Georgia Tech** (`LAUNCH_RECORD.md:30`),
so a GT-tenant login cannot be stood up before the demo.

**Decision:** every authentication path goes through one function,
`authenticate(request) -> Principal | None`, returning an authenticated subject
id. Two implementations are anticipated — a local stopgap now, and a
Clerk/Entra token adapter later — selected by configuration. No route reads the
raw cookie or the picker directly.

## Consequences
- Swapping providers is a config value plus one adapter, **not** a route
  rewrite; the rest of the app never learns which provider is in use.
- The person picker becomes admin-only or is deleted.
- "Stub Entra" means implementing this second adapter against a local/fake OIDC
  issuer for development — the seam already exists, so it is additive.
