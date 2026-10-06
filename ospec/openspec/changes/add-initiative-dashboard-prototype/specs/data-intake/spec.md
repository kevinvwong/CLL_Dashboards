# Spec Delta

## Purpose
Collect initiatives from leaders in one Excel template and load them safely, with clear reports of anything that breaks the taxonomy rules.

## ADDED Requirements

### Requirement: Generated intake template
The system SHALL generate `intake_template.xlsx` with one row per initiative and columns for code, name, description, level (dropdown), owner (dropdown), feeds (dropdown of active Dean codes), percent, status (dropdown), one X column per goal, one X column per priority, and one X column per Dean initiative.

*Amended 2026-10-06.* The requirement previously described the template as "code, name, description, owner (dropdown), level (dropdown), primary goal (dropdown), primary priority (dropdown), one X column per goal, ...". Three of those did not match what was built, and the three columns that were added to make the template usable at all were not described anywhere:

- **`Feeds`** carries the Dean codes a D-1 initiative feeds. `vw_DataChecks` flags "D-1 initiative not linked to any Dean initiative" and the importer refuses any workbook that leaves a check outstanding, so without this column no new D-1 initiative could ever be imported.
- **`Percent`** and **`Status`** carry a brand-new initiative's opening progress. The same gate flags "No progress update yet", so without them no new initiative could be imported either.
- The requirement named "primary goal (dropdown)" and "primary priority (dropdown)" columns. There are none, and nothing else marks primacy either: the X columns carry no primary/not distinction, and the importer inserts every goal and priority tag with `IsPrimary = 0`. So a workbook cannot say which goal or priority is primary, and an imported initiative ends with none. The UI still shows a "Primary" badge where the sample data has one. Recorded as a known gap below rather than papered over.

#### Scenario: Template reflects the database
- **WHEN** the template generator runs
- **THEN** dropdowns and X columns list the current goals, priorities, people, and Dean initiatives by name

#### Scenario: The columns that make a new initiative importable are present
- **WHEN** the template generator runs against the sample database
- **THEN** the Initiatives sheet has a `Feeds` column whose dropdown holds the active Dean codes
- **AND** it has `Percent` and `Status` columns, the Status dropdown holding the progress vocabulary
- **AND** a row that sets all three produces an initiative that clears `vw_DataChecks`

#### Scenario: A Dean row may not carry a Feeds value
- **WHEN** a row is marked Level `Dean` and also sets `Feeds`
- **THEN** the import is refused
- **AND** the report says a Dean initiative cannot feed another initiative, and quotes what it was given
- **AND** the message does not claim the value is missing, because it is not

#### Scenario: A D-1 row with no Feeds is refused by the data check
- **WHEN** a row is marked Level `D-1` and leaves `Feeds` empty
- **THEN** the import is refused
- **AND** the report names it as a D-1 initiative not linked to any Dean initiative

### Requirement: Primacy can be set after an import
Because the workbook cannot mark a goal or priority as primary (see the amendment note above), the system SHALL provide a way to set primacy on an imported initiative without importing again. The edit-tags screen SHALL offer a primary choice for each goal tag and each priority tag, and the system SHALL persist at most one primary per kind.

#### Scenario: An imported initiative has no primary
- **WHEN** an initiative is created by an import
- **THEN** none of its goal or priority tags is marked primary
- **AND** this is distinguishable from the sample data, which does carry primaries

#### Scenario: Primacy set through the edit screen persists
- **WHEN** an admin marks one of an imported initiative's goals as primary
- **THEN** the tag is stored with that goal marked primary
- **AND** reloading the card shows the "Primary" badge for it

#### Scenario: A second primary is still refused
- **WHEN** an admin marks a second goal as primary on the same initiative
- **THEN** the save is refused with the message the admin-editing spec requires
- **AND** the first primary is unchanged

### Requirement: Reference sheets in the template
The template SHALL include Goals, Priorities, and People sheets so the team can load goal and priority descriptions and the owner list in the same file.

#### Scenario: Descriptions loaded
- **WHEN** the Goals sheet has a full name and description for goal 3
- **THEN** after import the Research goal screen shows that full name and description

### Requirement: Progress preserved on re-import
Re-importing initiatives SHALL keep existing progress updates for any initiative whose code still exists.

#### Scenario: Re-import after updates
- **WHEN** owners have entered updates and the team re-imports a corrected template
- **THEN** every initiative that kept its code still shows its full diary

### Requirement: Validated import
The importer SHALL load a filled template into a temporary database, run all constraints and data checks, and replace the working database only when there are zero errors.

#### Scenario: Clean file
- **WHEN** a filled template has no errors
- **THEN** the working database is replaced and a summary of row counts is printed

#### Scenario: File with errors
- **WHEN** a row links a D-1 initiative to a non-Dean initiative
- **THEN** the import stops, the working database is unchanged, and the report names the sheet row and the problem

### Requirement: Data-checks page
The app SHALL show a `/checks` page listing every row of `vw_DataChecks` with a link to the affected initiative.

#### Scenario: Missing link reported
- **WHEN** a D-1 initiative has no Dean initiative link
- **THEN** `/checks` lists it with the issue "D-1 initiative not linked to any Dean initiative"
