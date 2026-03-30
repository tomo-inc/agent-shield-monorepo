# Week 1 Minimal Admin Panel — Requirements

> Version: v6.0
> Date: 2026-03-29
> Phase: Month 1 / Week 1

## 1. Goal

Deliver a minimal admin Panel in Week 1, allowing leads to view project onboarding status, the most recent check result, and any blocking reasons.

## 2. Scope

### Must deliver

- `apps/web` provides an accessible Panel page
- `apps/api` provides minimal result upload and query endpoints
- Local CLI and CI can upload check results
- Page displays: project overview, health status, most recent `check` result, last run time, blocking reason

### Out of scope

- Smoke test display
- Database
- Login and permission system
- Manual trigger execution
- Project configuration editing
- Historical trends
- Complex filtering and search

## 3. Data Flow

```text
CLI / CI
  ↓
POST /api/v1/panel/runs
  ↓
apps/api persists and aggregates
  ↓
GET /api/v1/panel/projects
  ↓
apps/web Panel display
```

## 4. Page Requirements

### Page 1: Project Status Overview

Fields:

| Field | Description |
|---|---|
| Project name | Project identifier |
| preset | Project type, e.g. `infer-monorepo`, `java-maven`, `custom` |
| Onboarding status | `ready / pending / blocked / custom-needed` |
| Health | `healthy / warning / failing / unknown` |
| check result | `pass / fail / timeout / blocked / not-run` |
| Last run time | Timestamp of the most recent result update |
| Block reason | Show `—` if no block |

Page requirements:

- Load data once on mount
- Provide a manual refresh button
- Table layout
- Status and health columns use color coding

## 5. API Requirements

### 5.1 Upload endpoint

`POST /api/v1/panel/runs`

Purpose:

- Local CLI or CI uploads one check result

Minimum fields:

- `project`
- `source`
- `git_ref`
- `git_sha`
- `triggered_by`
- `started_at`
- `finished_at`
- `status`
- `checks`
- `coverage_pct`
- `baseline_pct`
- `block_reason`

Requirements:

- Upload failure must not block the CLI main flow
- Upload failure must output a warning or log entry

### 5.2 Query endpoints

`GET /api/v1/panel/projects`

Purpose:

- Returns the Panel project overview list

`GET /api/v1/panel/projects/{project}/latest`

Purpose:

- Returns the most recent result for a single project

## 6. Aggregated Data

The Panel uses a unified aggregated result for display.

Suggested path:

- `.qa-agent/status/projects_status.json`

Alternatively, `apps/api` can return the same structure directly.

Schema:

```json
{
  "generated_at": "2026-03-29T02:00:00Z",
  "projects": [
    {
      "name": "wallet-service",
      "preset": "java-maven",
      "status": "ready",
      "health": "healthy",
      "check_all": "pass",
      "last_run_at": "2026-03-29T01:30:00Z",
      "block_reason": null
    }
  ]
}
```

## 7. Status Definitions

### Onboarding status

- `ready`: onboarded, executable
- `pending`: registered, onboarding not complete
- `blocked`: external blocker exists
- `custom-needed`: requires custom adaptation

### Check result

- `pass`: passed
- `fail`: failed
- `timeout`: timed out
- `blocked`: blocked
- `not-run`: has not been run

### Health derivation rules

| check_all | health |
|---|---|
| `pass` | `healthy` |
| `fail` | `failing` |
| `timeout` | `warning` |
| `blocked` | `warning` |
| `not-run` | `unknown` |

## 8. Technical Constraints

- Use `apps/web` to host the Panel
- Use `apps/api` to host upload and query endpoints
- No database
- Results are primarily persisted and aggregated via files
- Week 1 delivers a read-only dashboard only

## 9. Acceptance Criteria

- Panel page is accessible in the browser
- Local CLI results can be uploaded
- CI results can be uploaded
- Page displays all registered projects
- Page fields are consistent with aggregated results
- Health derivation rules are correct
- Leads can view overall status without entering the CLI

## 10. One-line Definition

> Week 1 delivers a minimal read-only admin Panel and adds CLI / CI result upload endpoints.
