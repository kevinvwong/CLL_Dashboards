# Architecture decisions (ADRs)

The dashboard's significant, hard-to-reverse decisions are recorded as short
Architecture Decision Records. Each states what was decided and why, so a future
reader does not "fix" something that was deliberate.

They live in the repository under `docs/adr/`. The list below is generated from
that folder at request time, so it cannot go out of step with the files.

## The decisions

- **ADR-0001 — Milestones hang off Priorities, not Team Initiatives.** A milestone
  evidences a Priority, because the Outcomes view is one card per priority.
- **ADR-0002 — Three status vocabularies stay distinct.** An initiative, a
  milestone and an outcome each have their own status set; unifying them would
  corrupt one of the three.
- **ADR-0003 — Identity colour is a code token, not a database column.** So a
  colour re-maps for the dark palette, and one map serves card, chip and cascade.
- **ADR-0004 — Authentication is a swappable adapter behind one Principal seam.**
  Every auth path goes through `authenticate(request)`; changing provider is one
  adapter, not a route rewrite.
- **ADR-0005 — Roles are local rows, not identity-provider groups.** Who you are
  comes from the provider; what you may do is held here.

Read the full text of each under `docs/adr/` in the repository.
