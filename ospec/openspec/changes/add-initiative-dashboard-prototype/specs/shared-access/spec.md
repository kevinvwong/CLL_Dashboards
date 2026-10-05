# Spec Delta

## Purpose
Make the prototype reachable by the Dean and D-1 leaders from their own computers, with a light access gate, so owners can enter updates before each Wednesday meeting.

## ADDED Requirements

### Requirement: Shared passcode gate
The app SHALL require a shared passcode, set by environment variable, before any page loads, and SHALL remember a successful entry in a signed cookie for 30 days.

#### Scenario: No passcode
- **WHEN** a visitor without the cookie opens any page
- **THEN** a passcode page is shown and no data is returned

#### Scenario: Correct passcode
- **WHEN** a visitor enters the correct passcode
- **THEN** they are sent to the person picker

### Requirement: Required person selection
After the passcode, the user SHALL pick who they are from active people before using the app; the choice is stored in a signed cookie and shown in the header with a Switch link.

#### Scenario: Picker before use
- **WHEN** a visitor has the passcode cookie but no person cookie
- **THEN** every page redirects to the person picker

### Requirement: Persistent data and backups
The app SHALL store the SQLite file on persistent disk at a configured path and SHALL write a timestamped copy of it at least once per day, keeping the last 14 copies.

#### Scenario: Daily backup
- **WHEN** the app has been running past the daily backup time
- **THEN** a new dated copy of the database exists in the backup folder and copies older than 14 days are removed

### Requirement: Single-command run
The app SHALL start with one command and SHALL read all settings (passcode, secret key, database path, backup path) from environment variables or a `.env` file.

#### Scenario: Fresh machine
- **WHEN** a developer installs requirements, builds the sample database, and runs the start command
- **THEN** the app serves on the configured port with no other setup

### Requirement: HTTPS on the live host
The live deployment SHALL serve only over HTTPS and SHALL set session cookies as Secure, HttpOnly, and SameSite=Lax.

#### Scenario: Plain HTTP request
- **WHEN** a visitor requests the live site over HTTP
- **THEN** they are redirected to HTTPS

### Requirement: Login lockout
The app SHALL block passcode attempts from an IP address for 15 minutes after 10 failed attempts within 15 minutes.

#### Scenario: Repeated wrong passcode
- **WHEN** an IP submits a wrong passcode 10 times in 15 minutes
- **THEN** the 11th attempt is refused with a "try again later" message even if the passcode is correct

### Requirement: Not indexed
The app SHALL send `X-Robots-Tag: noindex` on every response and serve a disallow-all `robots.txt`.

#### Scenario: Crawler visit
- **WHEN** a crawler requests `/robots.txt`
- **THEN** the response disallows all paths

### Requirement: Health check
The app SHALL expose `/healthz` outside the passcode gate, returning status 200 and no initiative data when the database is reachable.

#### Scenario: Deploy check
- **WHEN** the deploy script calls `/healthz` after a restart
- **THEN** it receives 200 with body `ok`

### Requirement: Separate environments
The app SHALL read `APP_ENV` (`local` or `live`) and SHALL show a visible "LOCAL" banner when running locally.

#### Scenario: Local banner
- **WHEN** the app runs with `APP_ENV=local`
- **THEN** every page shows a "LOCAL" banner so it is never mistaken for the live site
