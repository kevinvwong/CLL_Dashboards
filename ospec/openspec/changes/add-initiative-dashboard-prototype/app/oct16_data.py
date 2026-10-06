"""The October 16 deliverable data: the six Dean outcomes and their milestones.

Static by design. The brief for this view says 'Static, clickable pages; no live
data feeds', so the content lives here rather than in new tables. Values are the
wireframes' ILLUSTRATIVE figures - 'values show format only, not CLL results' -
and are replaced when owners confirm milestones and status on Oct 9-12.

Outcome names and target text are from the KPI workbook (07_CLL_KPI_Atomic_Definitions
_Master.xlsx, Metrics sheet). Milestones are from the wireframes' Option A page.

Generated from those two sources; do not hand-edit without re-reading them.
"""

# As-of date shown on the page. Set at the data cutoff (Oct 13).
AS_OF = None  # None renders “illustrative” instead of a false date

DATA_STATUS = "Illustrative — format only, not CLL results"

SOURCE_NOTE = (
    "Outcome names and targets: CLL KPI Atomic Definitions Master, Metrics sheet. "
    "Milestones: the October 16 wireframes, Option A. Status values are the "
    "wireframes' illustrative figures and are replaced when owners confirm."
)

# id, name, target text, executive summary, status, milestones-reached,
# milestones-planned, milestone list, and what it takes to show this
OUTCOMES = [
    {
        "id": 'P01',
        "name": 'One Shared Identity',
        "target": "All 4 teams adopt by Q2; ≥90% of reviewed assets aligned by Q4 (Dean's Blueprint)",
        "summary": '',
        "status": 'On track',
        "reached": 1,
        "planned": 4,
        "milestones": [
            {"name": 'Message architecture approved', "status": 'Met'},
            {"name": 'Teams adopted (1 of 4)', "status": 'In progress'},
            {"name": 'First asset audit', "status": 'Not started'},
        ],
    },
    {
        "id": 'P02',
        "name": 'Champion Innovation',
        "target": "≥6 pilots; ≥3 decisions; learning documented for 100% (Dean's Blueprint)",
        "summary": '',
        "status": 'On track',
        "reached": 2,
        "planned": 5,
        "milestones": [
            {"name": 'RDI baseline complete', "status": 'Met'},
            {"name": 'Innovation call launched', "status": 'Met'},
            {"name": 'First stage-gate decisions', "status": 'Due Dec'},
        ],
    },
    {
        "id": 'P03',
        "name": 'Integrated Portfolio & Pathways',
        "target": "≥2 badged pathways; 100% of new programs and credentials mapped; one approval workflow by Q2 (Dean's Blueprint)",
        "summary": '',
        "status": 'At risk',
        "reached": 1,
        "planned": 4,
        "milestones": [
            {"name": 'Unified approval process', "status": 'In progress'},
            {"name": 'First badged pathway', "status": 'In progress'},
            {"name": 'Mapping rule approved', "status": 'Met'},
        ],
    },
    {
        "id": 'P04',
        "name": 'Quality at Scale',
        "target": "≥20% reuse; ≤28-day average build; quality standard applied to 100% of scaled offerings (Dean's Blueprint)",
        "summary": '',
        "status": 'At risk',
        "reached": 0,
        "planned": 3,
        "milestones": [
            {"name": 'Quality standard approved', "status": 'Not started'},
            {"name": 'Reuse baseline', "status": 'In progress'},
            {"name": 'Build-time baseline', "status": 'Not started'},
        ],
    },
    {
        "id": 'P05',
        "name": 'Data-Informed Action',
        "target": "5 dashboards by Q2; owner, target and cadence for 100% of KPIs; monthly executive reviews (Dean's Blueprint)",
        "summary": '',
        "status": 'On track',
        "reached": 2,
        "planned": 4,
        "milestones": [
            {"name": 'KPI definitions drafted', "status": 'Met'},
            {"name": 'College dashboard', "status": 'This decision'},
            {"name": 'Owners named', "status": 'Not started'},
        ],
    },
    {
        "id": 'P06',
        "name": 'Culture & Learning',
        "target": "Operating models tested; quarterly learning reviews; ≥90% of priority commitments owned and current (Dean's Blueprint)",
        "summary": '',
        "status": 'On track',
        "reached": 1,
        "planned": 3,
        "milestones": [
            {"name": 'Target structure approved', "status": 'Confirm'},
            {"name": 'Q1 learning reviews', "status": 'In progress'},
            {"name": 'Operating model template', "status": 'Met'},
        ],
    },
]
