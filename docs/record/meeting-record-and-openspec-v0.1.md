<!--
  TRANSCRIPTION - do not edit by hand. Regenerate with:
      python scripts/transcribe_record.py

  Source of truth is the .docx beside this file. This is a complete
  transcription for search, diff and citation - nothing is summarised or
  omitted. Every paragraph and every table cell is reproduced in document
  order; run with --check to prove this file has not drifted from the .docx.
-->

# CLL Strategic Portfolio Dashboard
## Meeting Record, Change Control Package, and OpenSpec v0.1


COLLEGE OF LIFETIME LEARNING
Strategic Portfolio Dashboard
Meeting Record, Change Control Package, and OpenSpec v0.1

| Document Control | Value |
|---|---|
| Status | Draft authoritative project record for validation |
| Version | 0.1 |
| Prepared for | CLL Strategic Operations and leadership |
| Prepared by | Kevin Wong / Microsoft 365 Copilot-assisted synthesis |
| Source | User-provided meeting transcript; validated against the transcript in full |
| Confidentiality | Internal working document |
| Release purpose | Board demonstration readiness and controlled product evolution |


## Record integrity note

This package distinguishes confirmed meeting decisions from proposed future-state requirements. Percent-complete values were approved as the interim progress mechanism. Milestones were requested where feasible but were not established as a complete board-release dependency. Dates are recorded only as relative sequence because the transcript did not state calendar dates.

# Document Map

- 1. Executive Synopsis
- 2. Meeting Record
- 3. Decisions and Design Validations
- 4. Requirements Register
- 5. Change Request Register
- 6. Change Orders
- 7. OpenSpec v0.1
- 8. Action Items, Timeline, and Governance
- 9. Risks, Assumptions, Dependencies, and Open Questions
- 10. Traceability and Acceptance Framework
- Appendix A. Transcript-Derived Detail
- Appendix B. Terminology and Status Conventions

# 1. Executive Synopsis

The meeting reviewed a functional prototype of the CLL Strategic Portfolio Dashboard and established the next set of product, data, hosting, and presentation requirements. Leadership affirmed the overall direction: one connected portfolio model presented through Strategy 2035 goals, FY27 priorities, teams, and Dean-led initiatives. The immediate release is a board demonstration of the execution framework, not an audited reporting system. The longer-term product is better understood as a strategic portfolio operating platform than as a conventional dashboard.
The prototype already demonstrated valuable crosswalks among leadership initiatives, supporting team initiatives, organizational ownership, and strategic alignment. The group approved estimated percent complete as the near-term progress measure while more objective KPIs and milestones are developed. It also identified concrete navigation defects, density and usability issues, missing progress data, and incomplete people analytics. The spreadsheet remains the interim data conveyance method, with a proposed upload-and-refresh workflow before a full administrative interface is built.

# Outcome at a Glance


| Area | Meeting Outcome |
|---|---|
| Product direction | Proceed with the prototype and preserve the four-view information architecture. |
| Board release | Demonstrate value, strategic alignment, and execution visibility; avoid presenting incomplete data as authoritative. |
| Interim measurement | Use initiative-owner judgment to supply percent-complete values. |
| Milestones | Seek limited examples for demonstration; complete milestone design can follow the board release. |
| User experience | Add executive status summary, improve goal pages, support list/card switching, and correct routing defects. |
| Data administration | Continue spreadsheet-based updates in the near term; plan upload validation and automated refresh. |
| Infrastructure | Move from temporary/noninstitutional hosting constraints to the approved Georgia Tech Azure environment. |
| Future state | Develop objective metrics, capacity analytics, role-based experiences, and Microsoft ecosystem integrations. |


# 2. Meeting Record


# 2.1 Purpose

Review the prototype, determine whether its overall shape meets leadership intent, capture required changes, identify missing data, and establish a controlled path to a stable board demonstration.

# 2.2 Participants Referenced in the Transcript

- Kevin Wong: prototype lead and presenter.
- Elizabeth Smith: data owner and operating-model lead; responsible for coordinating initiative progress inputs.
- Bill Gaudelli: executive sponsor and primary board narrator.
- Cassie Parkin: Azure request support and planned internal reviewer.
- DeMarco Williams and Chris Reyes: planned internal review participants.
- Kathy: present at the opening; no substantive requirement attributed in the transcript.
Attendance and roles above are limited to what the transcript explicitly supports; the transcript does not provide a formal attendee roster.

# 2.3 Context and Hosting

The prototype was being demonstrated from the most current private development host because the Azure student-subscription deployment had low usage limits and was not reliable for repeated development deployments. The team had expedited an official Azure request. The stated intent was to move the work into a stable Georgia Tech environment so that the prototype could evolve rather than be discarded.
The transcript includes a disclosure that a student Azure account was used as a temporary workaround. This record does not endorse that workaround. The controlled requirement is to migrate the application and data to an approved institutional environment and discontinue reliance on personal or student-hosted resources.

# 2.4 Prototype Demonstration

- The dashboard opens with common content for all users, with future personalization proposed for the Dean, data owner, leaders, and other roles.
- Users can access initiatives, priorities, teams, Strategy 2035 goals, Dean initiatives, and items requiring review.
- The same underlying data is represented through four principal organizational views.
- The initiative register includes major initiatives and ownership/relationship information.
- Drill-down cards show strategic alignment, descriptions, owners, and intended progress information.
- The prototype successfully displayed a Dean initiative and the team initiatives supporting it, which leadership explicitly found helpful.

# 2.5 Data and Measurement Discussion

The meeting clarified that initiatives roll up to priorities, but the organization does not yet have a complete set of initiative-level metrics or priority milestones. Leadership therefore approved owner-provided percent complete as the interim operating measure. Objective measures remain the desired future state. Milestones are expected to improve priority-level reporting, but complete milestone definition requires a collaborative exercise and may follow the board meeting.

# 2.6 User Experience Discussion

- The initiative list is too dense and requires improved navigation.
- Goal views should display full Strategy 2035 goal language rather than abbreviated labels.
- The visual identity of the cleaner initiative/outcome cards should be reused across views.
- A list/card toggle should let users choose the representation appropriate to the number of initiatives.
- A compact summary or telemetry row should appear above detailed content so leaders can acquire status quickly.
- The design should serve the majority of portfolio areas rather than be dominated by the unusually large academic-goal initiative count.
- The Source Area field may remain in the data model but should be hidden from the user interface now that the crosswalk transition has been communicated.

# 2.7 Defects Observed During the Demonstration


| Defect | Observed Behavior | Expected Behavior |
|---|---|---|
| Initiative route failure | Selecting Consult GT returned the user to the full initiative list. | Open the selected initiative detail and its supporting initiatives. |
| Unexpected side modal | Selecting reusable content produced a surprising side panel/modal behavior. | Open content consistently without unexpected overlays or loss of context. |
| Inconsistent drill-down | Some initiative selections opened detail correctly while others did not. | All portfolio objects use consistent drill-down rules. |
| Incomplete progress display | Bars showed no data where metrics or checkpoints were absent. | Display interim progress, milestone placeholders, or a clear data-not-yet-defined state. |
| Overloaded register view | The initiative register was described as jam-packed. | Offer scanning, filtering, and alternative representations without visual overload. |


# 2.8 People, Capacity, and Future Automation

Leadership wants the People view to provide a high-level picture of activity and capacity, including where work is concentrated, where labor shortages may exist, and where additional resources may be needed. The stated purpose is portfolio and capacity management, not surveillance. Future concepts included connecting Planner, Teams, Outlook, Copilot, meeting transcripts, and other activity signals so that decisions, completed work, and progress might be surfaced with less manual data entry. These concepts were directional and were not approved as current-release commitments.

# 2.9 Board Demonstration Plan

The board presentation should introduce the platform and its benefit, explain how strategy cascades into execution, and follow a rehearsed navigation path that avoids dead ends. Bill is expected to explain the purpose and operating vision while Elizabeth can drive the interface. Kevin offered to support a rehearsal and the meeting itself if needed. The group proposed a short introduction of approximately ten minutes, but no final presentation script or exact duration was approved.

# 3. Decisions and Design Validations


| ID | Decision | Status | Record |
|---|---|---|---|
| D-001 | Proceed with the prototype | Approved | The general shape and direction were affirmed. |
| D-002 | Retain four-view model | Approved | Organize common portfolio data by Strategy 2035 goals, FY27 priorities, teams, and Dean initiatives. |
| D-003 | Use spreadsheet as interim data conveyance | Approved | Continue workbook updates until a controlled administrative workflow is available. |
| D-004 | Adopt percent complete as interim progress measure | Approved | Owner judgment supplies a practical measure until objective KPIs exist. |
| D-005 | Treat board version as demonstration release | Approved | Focus on concept, benefit, and execution model rather than exhaustive data reporting. |
| D-006 | Seek limited milestone exemplars | Approved with constraint | Use a small number of draft examples if feasible; do not require complete milestone definition for every item before the board demo. |
| D-007 | Add list/card switching | Approved direction | Support high-density and visual browsing modes. |
| D-008 | Add executive summary/telemetry | Approved direction | Provide rapid portfolio-status acquisition above detailed views. |
| D-009 | Hide Source Area in UI, retain underlying data | Approved direction | Preserve transition history without cluttering the current interface. |
| D-010 | Optimize for representative use cases | Approved principle | Do not let the largest academic portfolio view dictate every layout. |
| D-011 | Preserve Dean-to-team initiative crosswalk | Validated | Leadership specifically valued seeing supporting work together. |
| D-012 | Separate board-release stabilization from editing capability | Approved sequence | Finalize information shape and stable navigation before building full data-maintenance features. |
| D-013 | Move to approved Azure hosting | Required direction | Eliminate reliance on constrained or noninstitutional hosting for ongoing work. |


# 4. Requirements Register


| ID | Requirement | Horizon | Priority |
|---|---|---|---|
| FR-001 | Present the portfolio through goals, priorities, teams, and Dean initiatives. | Current/Refine | High |
| FR-002 | Provide drill-down from each portfolio object without losing context. | Current/Defect | Critical |
| FR-003 | Display full Strategy 2035 goal descriptions. | Board release | High |
| FR-004 | Display initiative owner, description, alignments, progress, and supporting initiatives. | Board release | High |
| FR-005 | Capture and display initiative percent complete. | Board release | Critical |
| FR-006 | Support priority milestones and milestone completion states. | Incremental | High |
| FR-007 | Support list and card views. | Board release | High |
| FR-008 | Provide an executive telemetry layer with status, review needs, and upcoming milestones where data exists. | Board release | High |
| FR-009 | Hide Source Area from standard views while retaining it in stored data. | Board release | Medium |
| FR-010 | Show traceability from Dean initiatives to supporting team initiatives. | Board release | High |
| FR-011 | Support role-based experiences for Dean, data owner, team leaders, and contributors. | Future | Medium |
| FR-012 | Support spreadsheet upload, validation, and refresh. | Near term | High |
| FR-013 | Provide administrative editing after the information model stabilizes. | Future | Medium |
| FR-014 | Represent data-not-defined states without misleading zero progress. | Board release | High |
| FR-015 | Provide people-to-initiative relationships. | Current/Refine | Medium |
| FR-016 | Support future workload and capacity analysis without individual surveillance. | Future | Medium |
| FR-017 | Support future objective metrics and KPI rollups. | Future | High |
| FR-018 | Support future ingestion of decisions, actions, and status signals from Microsoft 365 sources. | Future discovery | Low |
| NFR-001 | Operate in an approved Georgia Tech hosting environment. | Immediate | Critical |
| NFR-002 | Remain stable during board demonstration; control changes through a freeze and rehearsal. | Board release | Critical |
| NFR-003 | Make executive status understandable within seconds. | Board release | High |
| NFR-004 | Provide consistent navigation and visual language across object types. | Board release | High |
| NFR-005 | Preserve data lineage and avoid representing subjective progress as objective KPI data. | All phases | Critical |


# 5. Change Request Register


| ID | Change Request | Priority | Status | Target |
|---|---|---|---|---|
| CR-001 | Add percent-complete field and progress display | Critical | Open | Board release |
| CR-002 | Add milestone model and exemplars | High | Open | Incremental |
| CR-003 | Add card/list toggle | High | Open | Board release |
| CR-004 | Add executive summary/telemetry row | High | Open | Board release |
| CR-005 | Redesign Strategy 2035 goal pages | High | Open | Board release |
| CR-006 | Correct initiative routing and inconsistent drill-down | Critical | Open | Board release |
| CR-007 | Create workbook upload/validation/refresh workflow | High | Proposed | Near term |
| CR-008 | Expand People view relationships | Medium | Proposed | Near term |
| CR-009 | Define objective KPI architecture | High | Deferred | Future |
| CR-010 | Correct unexpected modal/overlay behavior | High | Open | Board release |
| CR-011 | Hide Source Area in standard UI | Medium | Open | Board release |
| CR-012 | Preserve Dean-to-team initiative crosswalk | High | Validated | Board release |
| CR-013 | Add role-based dashboard experiences | Medium | Deferred | Future |
| CR-014 | Add workforce capacity analytics | Medium | Discovery | Future |
| CR-015 | Define Microsoft 365 activity-ingestion architecture | Low | Discovery | Future |
| CR-016 | Replace static homepage counts with meaningful timing/status indicators | High | Open | Board release |
| CR-017 | Improve no-data and coming-soon states | High | Open | Board release |
| CR-018 | Create a rehearsed board-demo navigation path | Critical | Open | Board release |


# 6. Change Orders


| Order | Title | Scope | Intended Outcome |
|---|---|---|---|
| CO-001 | Board Release UX Stabilization | Routing fixes, consistent drill-down, goal-view redesign, list/card toggle, density reduction, no-data states. | Stable, coherent demonstration path. |
| CO-002 | Interim Progress Measurement | Workbook percent-complete field, progress display, labeling of subjective inputs. | Usable progress reporting before KPI maturity. |
| CO-003 | Milestone Planning Layer | Milestone definitions, priority rollups, exemplar records, placeholders. | Transparent future progress model. |
| CO-004 | Executive Telemetry Layer | Portfolio health summary, review flags, milestone timing, at-risk indicators where supported. | Rapid leadership comprehension. |
| CO-005 | Data Administration Bridge | Workbook schema, upload, validation, error handling, refresh, version record. | Reduced manual rework and reproducible updates. |
| CO-006 | Role and Access Model | Personalized views, permissions, data-owner controls, Dean authorities to be defined separately. | Controlled stakeholder experiences. |
| CO-007 | Portfolio Capacity Analytics | People-initiative mapping, workload concentration, shortage indicators, resource-analysis safeguards. | Resource planning without surveillance. |
| CO-008 | Microsoft Ecosystem Integration Discovery | Planner, Teams, Outlook, Copilot, and transcript-derived activity concepts. | Validated future architecture and governance requirements. |
| CO-009 | Institutional Hosting Transition | Migrate application and data into approved Azure resources and retire temporary hosting. | Stable, supportable institutional deployment. |


# 7. OpenSpec v0.1


# 7.1 Product Definition

The CLL Strategic Portfolio Dashboard is the first release of a strategic portfolio operating platform that connects institutional strategy to priorities, leadership initiatives, team initiatives, people, progress, and future operational signals. The board release demonstrates this model. It does not yet constitute a complete system of record, objective KPI platform, workforce evaluation tool, or automated performance-management system.

# 7.2 Product Objectives

- Make the strategy-to-execution cascade visible.
- Provide multiple views of one governed portfolio model.
- Enable leadership to identify progress, alignment, gaps, and review needs quickly.
- Establish traceable relationships among goals, priorities, initiatives, teams, and people.
- Create a practical bridge from spreadsheet administration to a governed application.
- Prepare the architecture for later objective metrics and Microsoft 365 integration.

# 7.3 Out of Scope for Board Release

- Complete initiative editing inside the application.
- Automated KPI computation for all initiatives.
- Complete milestone definitions for every priority or initiative.
- Automated performance evaluation or employee surveillance.
- Production-grade transcript ingestion or Planner synchronization.
- Finalized role permissions beyond what is needed to demonstrate the concept.

# 7.4 Core Entities and Relationships


| Entity | Minimum Attributes | Relationships |
|---|---|---|
| Strategy Goal | ID, full title, official description | Many-to-many with priorities and initiatives where supported. |
| Annual Priority | ID, title, description, milestone set, status | Linked to goals and major initiatives. |
| Dean Initiative | ID, title, description, owner, progress | Linked to priorities and supporting team initiatives. |
| Major/Team Initiative | ID, title, description, owner/team, percent complete, update | Linked to goals, priorities, Dean initiatives, and people. |
| Team | ID, name, current/legacy source area where retained | Owns or supports initiatives. |
| Person | ID, name, role, team | Owns or contributes to initiatives; future capacity relationship. |
| Milestone | ID, parent object, description, target, status | Supports priority or initiative progress concept. |
| Progress Update | Parent ID, percent complete, narrative, update date, source | Interim subjective update; later supplemented by objective data. |


# 7.5 Data Governance

- The workbook is the interim controlled input and must use stable IDs for all records.
- Percent complete must be labeled as an owner estimate or leadership judgment, not as an objective KPI.
- Undefined progress must not be displayed as zero unless zero is an explicit value.
- Legacy Source Area may be retained for lineage while hidden from standard user views.
- Every refresh should preserve the prior input version, validation result, and refresh outcome.
- Future automated signals require source, timestamp, confidence, review, and correction controls.

# 7.6 Role Model


| Role | Near-Term Experience | Future Controls |
|---|---|---|
| Dean | Executive overview, priorities, Dean initiatives, strategic drill-down. | Approval/escalation powers to be separately defined. |
| Data Owner / Strategic Operations | Portfolio-wide view and controlled data stewardship. | Upload, validation, editing, release, and audit controls. |
| Team Leader | Team and related strategic views. | Submit updates; manage assigned initiative data subject to governance. |
| Contributor | Relevant initiative and personal work context. | Update authorized tasks or progress inputs. |
| Viewer | Read-only board/leadership experience. | Role-specific filtering and sharing controls. |


# 7.7 Board Release Acceptance Criteria


| ID | Acceptance Criterion |
|---|---|
| AC-001 | Official Azure-hosted or otherwise approved stable demonstration endpoint is available. |
| AC-002 | No board-demo navigation path reaches a known dead end or incorrect full-list redirect. |
| AC-003 | All initiatives intended for demonstration have a description, owner/context, and valid relationships. |
| AC-004 | Percent-complete values are loaded where supplied and clearly identified as interim estimates. |
| AC-005 | Undefined values display as not yet defined or coming soon, not misleading zero values. |
| AC-006 | Strategy 2035 goal views show full goal descriptions. |
| AC-007 | List and card presentations are usable for both high- and low-volume goal areas, or a controlled alternative is available. |
| AC-008 | Executive summary indicators reflect real loaded data and avoid static decorative counts. |
| AC-009 | A rehearsed demonstration route and presenter handoff are documented. |
| AC-010 | Release is frozen before rehearsal; only critical corrections are admitted afterward. |


# 7.8 Future Architecture Principles

- Atomize data from fields to metrics, KPIs, priority measures, and strategic outcomes.
- Prefer natural operational data where available, while retaining governed human judgment for qualitative work.
- Keep role-based permissions, privacy, and correction mechanisms explicit.
- Do not infer employee performance from activity exhaust. Capacity analytics must remain portfolio-focused and human-reviewed.
- Treat meeting and collaboration content as governed source material, not automatically authoritative truth.
- Integrate through stable IDs and auditable interfaces rather than brittle screen-level automation.

# 8. Action Items, Timeline, and Governance


| ID | Action | Owner | Timing | Priority |
|---|---|---|---|---|
| AI-001 | Coordinate percent-complete input for all initiatives. | Elizabeth / team leaders | Immediate | Critical |
| AI-002 | Seek a limited set of draft milestones, ideally 3-5 where feasible. | Elizabeth / leadership team | Before board demo if capacity permits | High |
| AI-003 | Correct route and modal defects. | Kevin | Weekend revision cycle | Critical |
| AI-004 | Redesign goal and high-density initiative views. | Kevin | Weekend revision cycle | High |
| AI-005 | Add meaningful summary/telemetry content and remove static counts. | Kevin | Before internal review | High |
| AI-006 | Hide Source Area from standard UI while preserving stored data. | Kevin | Before internal review | Medium |
| AI-007 | Run internal flow and visual review. | Cassie, DeMarco, Chris | Monday in transcript sequence | High |
| AI-008 | Return consolidated feedback to Elizabeth. | Strategic Operations | Tuesday in transcript sequence | High |
| AI-009 | Freeze release changes. | Kevin / Strategic Operations | Wednesday in transcript sequence | Critical |
| AI-010 | Conduct board rehearsal and confirm presenter handoff. | Bill, Elizabeth, Kevin | Thursday in transcript sequence | Critical |
| AI-011 | Deliver board demonstration. | Bill and Elizabeth; Kevin support as needed | Friday in transcript sequence | Critical |
| AI-012 | Define post-board milestone and KPI work plan. | Strategic Operations / leadership | Post-board | High |
| AI-013 | Document approved Azure deployment and retire temporary host. | Kevin / institutional IT partners | As provisioning completes | Critical |

Timing note: The transcript names weekdays but not calendar dates. The sequence above is preserved without inventing dates.

# Release Governance

- Before freeze: accept approved scope and defect corrections.
- After freeze: admit only changes necessary for demonstration stability or material factual accuracy.
- Rehearsal: validate navigation, content, presenter handoffs, timing, and fallback path.
- Board release: identify the application as a demonstration and explain which data is interim.
- Post-board: convert feedback into controlled change requests rather than modifying requirements informally.

# 9. Risks, Assumptions, Dependencies, and Open Questions


| ID | Type | Statement | Treatment |
|---|---|---|---|
| R-001 | Risk | Incomplete KPI framework may cause subjective progress to be mistaken for objective performance. | Label percent complete as interim estimate and preserve source. |
| R-002 | Risk | Incomplete milestones may leave priority views visually sparse. | Use limited exemplars and explicit coming-soon states. |
| R-003 | Risk | Known navigation defects could undermine board confidence. | Fix, regression-test, freeze, and rehearse. |
| R-004 | Risk | Spreadsheet version drift may create inconsistent displays. | Create versioned upload and validation controls. |
| R-005 | Risk | Temporary hosting may fail or fall outside institutional expectations. | Transition to approved Azure environment. |
| R-006 | Risk | People analytics could be perceived or used as surveillance. | Adopt purpose limitation, aggregation, access controls, and human review. |
| R-007 | Risk | Automated activity ingestion may misattribute work or decisions. | Require provenance, confidence, correction, and approval. |
| A-001 | Assumption | The initiative spreadsheet contains stable identifiers and baseline descriptions. | Validate before automated refresh. |
| A-002 | Assumption | Leadership can provide percent-complete estimates for the intended board dataset. | Track missing values explicitly. |
| D-001 | Dependency | Approved Azure resources and access. | Confirm deployment readiness and support ownership. |
| D-002 | Dependency | Leadership input for percent complete and milestones. | Coordinate through the controlled workbook. |
| Q-001 | Open question | What exact indicators belong in the executive telemetry row? | Decide based on available, reliable board-release data. |
| Q-002 | Open question | How should initiative rollups be calculated when measures differ? | Define KPI and aggregation policy after board release. |
| Q-003 | Open question | What final permissions and escalation powers should the Dean hold? | Resolve through separate role/workflow governance. |
| Q-004 | Open question | Which event is the authoritative meeting record to which this package should be attached? | Confirm before attaching or publishing to a meeting record. |


# 10. Traceability and Acceptance Framework


| Transcript Theme | Decision/Requirement | Change Control | Acceptance Evidence |
|---|---|---|---|
| Four ways to view work | D-002; FR-001 | CO-001 | All four views load from the same model. |
| Gut-check percent complete | D-004; FR-005 | CR-001; CO-002 | Workbook values display with interim label. |
| Milestones unavailable | D-006; FR-006 | CR-002; CO-003 | Exemplars or explicit not-yet-defined state. |
| Dense goals and cards | D-007; FR-007 | CR-003; CO-001 | List/card controls or equivalent tested. |
| Quick status acquisition | D-008; FR-008 | CR-004; CO-004 | Summary indicators are data-backed and readable. |
| Consult GT redirect | FR-002 | CR-006; CO-001 | Selected initiative opens correct detail. |
| Unexpected modal | FR-002; NFR-004 | CR-010; CO-001 | No unintended overlay in regression test. |
| Source Area no longer needed onscreen | D-009; FR-009 | CR-011 | Field hidden in UI, retained in data. |
| Dean/team crosswalk praised | D-011; FR-010 | CR-012 | Supporting initiatives appear together. |
| Spreadsheet upload idea | D-003; FR-012 | CR-007; CO-005 | Validation and refresh test succeeds. |
| People and labor shortage questions | FR-016 | CR-014; CO-007 | Future discovery defines safe capacity measures. |
| Planner/Copilot/transcript concepts | FR-018 | CR-015; CO-008 | Architecture discovery includes governance controls. |
| Board demo and rehearsal | D-005; NFR-002 | CR-018 | Rehearsal completed on frozen build. |


# Appendix A. Transcript-Derived Detail


# A.1 Confirmed Positive Reactions

- Leadership repeatedly said the prototype looked strong and was moving in the right direction.
- The clean card layout and quick visual progress cue were specifically praised.
- The crosswalk displaying a leadership initiative with supporting team initiatives was described as especially helpful.
- List/card switching and a summary status layer were welcomed as solutions to information overload.

# A.2 Data Requested from Leadership

- Percent complete for each initiative.
- A limited set of illustrative milestones if capacity allows.
- Continued updates in the existing spreadsheet during the interim phase.

# A.3 Presentation Guidance

- Follow a clear path that shows the fullest and most stable version of the product.
- Avoid dead ends and unstable navigation.
- Explain why the dashboard exists, how it supports execution, and how it will cascade through the organization.
- Demonstrate concept and benefit rather than interrogating incomplete data.

# A.4 Longer-Term Vision Signals

- Objective measures that vary appropriately by initiative type.
- Progressive rollup from atomic data to metrics, KPIs, priorities, and goals.
- Resource-capacity insight at a suitable level of aggregation.
- Microsoft Planner and Copilot-supported work management.
- Potential extraction of decisions and actions from meeting transcripts and collaboration activity.

# Appendix B. Terminology and Status Conventions


| Term | Meaning in This Package |
|---|---|
| Approved | Explicitly accepted in the meeting or clearly agreed as the immediate direction. |
| Approved direction | Concept accepted; design details remain to be finalized. |
| Validated | Existing capability received positive confirmation and should be preserved. |
| Proposed | Raised as a useful approach but not fully approved or specified. |
| Deferred/Future | Not part of the immediate board release. |
| Critical | Necessary for release stability, integrity, or institutional hosting. |
| Percent complete | Subjective interim estimate supplied by accountable leadership or initiative owner. |
| Milestone | Defined intermediate outcome or checkpoint; not yet complete across the portfolio. |
| Telemetry layer | Compact executive summary designed for rapid acquisition of portfolio health. |
| OpenSpec | The controlled product specification integrating scope, requirements, governance, and acceptance criteria. |
