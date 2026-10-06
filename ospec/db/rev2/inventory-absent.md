# No approved initiative inventory exists

Task 1.4. Recorded because it changes what the build can honestly claim.

## Summary

The package ships **canonical strategy** and **zero operational data**. There is
no approved list of Dean initiatives, D-1 initiatives, people, ownership
assignments, updates or metrics anywhere in it. Counts below were read from
`03_Strategy_Portfolio_Data_Package.xlsx` when this note was written.

## What is loaded

| Sheet | Data rows |
|---|---|
| `Goals` | 5 |
| `StrategicObjectives` | 25 |
| `Priorities` | 6 |
| `CanonicalTargets` | 11 |
| `SourceRegister` | 5 |
| `ControlledVocab` | 36 |
| `AcceptanceCriteria` | 10 |

## What is empty

Every sheet that would carry operational portfolio data has a header row and
nothing else:

| Sheet | Data rows |
|---|---|
| `Initiatives` | 0 |
| `People` | 0 |
| `Teams` | 0 |
| `InitiativeGoals` | 0 |
| `InitiativePriorities` | 0 |
| `InitiativeRelations` | 0 |
| `Ownership` | 0 |
| `Updates` | 0 |
| `Metrics` | 0 |
| `InitiativeMetrics` | 0 |
| `GoalMetrics` | 0 |

## What the package itself says

Its readiness table (`11_READ_ME_FIRST.md` section 5) lists these as **Pending
business validation**:

- Dean Initiative inventory
- D-1 Initiative inventory
- Ownership and stewardship assignments
- Metric definitions and authoritative sources
- Executive and governance signoff

The Business Data Validation Register says the same in numbers: one open issue
per category (`ISS-001` to `ISS-010`), all `Open`, no `DecisionDate`, and no
signatures on `Issues-Signoff`. Its `Summary` sheet is live formulas whose
cached values are all zero, so every readiness percentage currently computes to
0 percent.

## Consequence

- The prototype's 22 initiatives are **this project's invention**. They are not
  a migration source, and no approved inventory exists to migrate from. Task 8.2
  relabels them as synthetic.
- Schema work can proceed and can be tested against synthetic data. Production
  migration cannot, and no task in this change claims otherwise.
- All ten acceptance criteria in the package read `Not Tested` with empty
  evidence. Conformance must not be claimed until they are executed (task 7.1).
