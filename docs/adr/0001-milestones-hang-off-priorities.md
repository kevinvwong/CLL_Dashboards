# Milestones hang off Priorities, not Team Initiatives

**Status:** accepted (2026-10-07)

A **Milestone** is a concrete, checkable event that evidences a **Priority**
(`P01`–`P06`), not a Team Initiative. This is counter-intuitive because the
register's volume of work lives on the 29 Team Initiatives, so the obvious
placement is a milestone-per-initiative. But the `/outcomes` view this serves is
one card per **Priority** (the six Dean-level outcomes), and its
"milestones reached / planned" figure is defined per outcome (workbook rows
A-16/A-17). Each milestone therefore links to one Priority; the Team Initiatives
remain a separate roll-up layer.

## Consequences
- `Milestones.PriorityCode` references `Priorities`; there is no
  `Milestones.MIId`.
- A Priority's progress is `count(Status = 'Met') / count(all)` for its
  milestones, exposed as `vw_PriorityMilestoneProgress`.
- Do not "fix" this by moving milestones under Team Initiatives; the Outcomes
  card is the reason the edge points at the Priority.
