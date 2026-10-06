# Spec Delta

## Purpose

Defines the recorded procedure for deploying and rolling back the live service, and the rule that its success is judged by what the running service reports rather than by what the deploying command returns.

## ADDED Requirements

### Requirement: Deploy success is judged by the service, not the command
Whether a deploy succeeded SHALL be determined by probing the running service, and SHALL NOT be determined by the deploying command's exit status. A deploy SHALL be verified by observing the service report the revision that was just deployed.

#### Scenario: A command reporting failure is not treated as failed
- **WHEN** the deploy command exits non-zero but the service reports the new revision
- **THEN** the deploy is treated as successful
- **AND** the failure is recorded as a reporting artefact of the tooling, not a deploy failure

#### Scenario: A command reporting success is not trusted alone
- **WHEN** the deploy command reports success
- **THEN** the service is probed before the deploy is called successful
- **AND** a service that still reports the previous revision is treated as a failed deploy

#### Scenario: The deployed revision is identifiable
- **WHEN** the service is probed after a deploy
- **THEN** it reports which revision it is serving
- **AND** that value distinguishes this deploy from the one before it

### Requirement: The deploy is recorded and repeatable
The deploy SHALL follow a written procedure that another person can execute without reconstructing it from history. Every input the procedure needs SHALL be recorded, including how the deployment archive is built and what it must and must not contain.

#### Scenario: The archive's contents are defined
- **WHEN** the deployment archive is built
- **THEN** the procedure states what it must contain
- **AND** it states what must be excluded, including anything that would overwrite live data

#### Scenario: A fresh operator can deploy
- **WHEN** someone follows the recorded procedure on a machine that has never deployed
- **THEN** they can produce the archive and deploy it
- **AND** they do not need to ask what a step meant

#### Scenario: The procedure's prerequisites are named
- **WHEN** the procedure is followed
- **THEN** the credentials and tools it needs are named
- **AND** they are not embedded in the procedure itself

### Requirement: The live database is never overwritten by a deploy
A deploy SHALL NOT replace the live service's data with a local copy. Where the deployment archive contains a database, the procedure SHALL state why and what happens to the live data.

#### Scenario: Live data survives a deploy
- **WHEN** a deploy completes
- **THEN** the data the service was serving before the deploy is still present
- **AND** any updates made before the deploy remain

#### Scenario: A deploy that would destroy live data is detectable
- **WHEN** an archive is prepared that would overwrite live data
- **THEN** the procedure identifies it before it is deployed
- **AND** it is not deployed

### Requirement: Rollback is recorded before it is needed
The rollback SHALL be written down before any launch, and SHALL return the service to a known previous state including its data. It SHALL NOT require reconstructing anything from memory or from a developer's local machine.

#### Scenario: Rollback restores the previous revision
- **WHEN** a rollback is executed
- **THEN** the service serves the revision that was live before the launch
- **AND** the service is reachable afterwards

#### Scenario: Rollback restores the previous data
- **WHEN** a launch loaded new data and is rolled back
- **THEN** the previous dataset is restored
- **AND** the service's figures match what they were before the launch

#### Scenario: Rollback is exercised before launch
- **WHEN** the launch procedure is prepared
- **THEN** the rollback has been performed at least once
- **AND** it is not being attempted for the first time during an incident
