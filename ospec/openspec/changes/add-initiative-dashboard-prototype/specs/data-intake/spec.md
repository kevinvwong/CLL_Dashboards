# Spec Delta

## Purpose
Collect initiatives from leaders in one Excel template and load them safely, with clear reports of anything that breaks the taxonomy rules.

## ADDED Requirements

### Requirement: Generated intake template
The system SHALL generate `intake_template.xlsx` with one row per initiative and columns for code, name, description, owner (dropdown), level (dropdown), primary goal (dropdown), primary priority (dropdown), one X column per goal, one X column per priority, and one X column per Dean initiative.

#### Scenario: Template reflects the database
- **WHEN** the template generator runs
- **THEN** dropdowns and X columns list the current goals, priorities, people, and Dean initiatives by name

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
