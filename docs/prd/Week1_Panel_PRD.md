# Week 1 Minimal Admin Panel — Requirements

> Version: v7.3
> Date: 2026-03-30
> Phase: Month 1 / Week 1

## 1. Goal

Deliver a minimal admin Panel in Week 1, allowing leads to view project onboarding status, the most recent check result, and any blocking reasons.

## 2. Scope

### Must deliver

- This PRD must reflect actual Week 1 data produced by the CLI flow
- Panel data model must be compatible with `agentshield check`, `agentshield init --yes`, `agentshield baseline update`, and `agentshield report`
- Page displays: project overview, latest run result, per-module summary, coverage gate outcome, last run time, and blocking reason
- Week 1 source data comes from CLI-generated config, run history, and baseline files
- `apps/api` provides CLI write endpoints and Panel read endpoints, and persists Panel query data into a database

### Out of scope

- Smoke test display
- Login and permission system
- Manual trigger execution
- Project configuration editing
- Historical trends
- Complex filtering and search
- Replacing CLI file outputs as the Week 1 source of truth

## 3. Data Flow

```text
agentshield init / baseline update / check
  ↓
CLI writes local `.agentshield/*` artifacts
  ↓
CLI calls apps/api write endpoints
  + POST /api/v1/panel/projects/register
  + POST /api/v1/panel/baselines
  + POST /api/v1/panel/runs
  ↓
apps/api validates and writes DB rows
  ↓
apps/web Panel display
```

## 4. Page Requirements

### Page 1: Project Status Overview

Fields:

| Field | Description |
|---|---|
| Project name | Project identifier from config |
| preset | Project type, e.g. `infer-monorepo`, `java-maven`, `custom` |
| Module count | Number of detected sub-modules, e.g. `apps/api`, `apps/web` |
| Onboarding status | Derived from actual Week 1 state: `ready / pending / blocked / custom-needed` |
| Health | Derived from latest aggregated check result: `healthy / warning / failing / unknown` |
| check result | Latest aggregated project result: `pass / fail / timeout / blocked / not-run` |
| Last run time | Timestamp of the most recent result update |
| Coverage summary | Show current line coverage and gate threshold when available |
| Block reason | Show `—` if no block |

Per-project expanded detail should show:

- sub-module name, e.g. `apps/api`, `apps/web`
- detected stack summary, e.g. `Python / FastAPI`, `TypeScript / Next.js`
- checker results for `build`, `lint`, `typecheck`, `test`, `coverage`
- coverage parser type when available, e.g. `pytest-cov-json`, `istanbul-json`, `jacoco-xml`
- baseline comparison result for each module
- strict-mode blocking reason when the latest run failed the gate

Page requirements:

- Load data once on mount
- Provide a manual refresh button
- Table layout
- Status and health columns use color coding

## 5. Week 1 Data Contract

Week 1 does not treat database records as the original source of truth. CLI local artifacts still exist, but the Panel path uses CLI write endpoints to persist data into the DB query store.

For this PRD, `.agentshield/` is the canonical Week 1 runtime directory naming used for config, runs, and baselines.

### 5.1 Source files

- `.agentshield/config.yaml`
- `.agentshield/runs/*.json`
- `.agentshield/baselines/*.json`

Minimum meaning of each file type:

- `config.yaml`: project identity, preset, command overrides, thresholds, timeouts, notification settings
- `runs/*.json`: one full run record, including module-level check results and overall aggregated result
- `baselines/*.json`: per-module baseline coverage used to derive coverage gate

### 5.2 CLI write endpoints

Week 1 requires 3 CLI write endpoints:

- `POST /api/v1/panel/projects/register`
  used after project initialization to upload project config and module list
- `POST /api/v1/panel/baselines`
  used after initial baseline collection or `baseline update`
- `POST /api/v1/panel/runs`
  used after each `agentshield check`

Call timing:

- `projects/register`: after `config.yaml` is successfully written
- `baselines`: after baseline files are successfully written
- `runs`: after the run result file is successfully written

Requirements:

- write endpoint failure must not block the CLI main flow
- CLI must emit a warning or log entry
- repeated uploads must be idempotent

### 5.3 Database persistence target

The Panel layer must persist a database-backed query model from the data uploaded by CLI through the write endpoints above.

Requirements:

- DB is the Panel query store
- writes must be idempotent
- repeated uploads must update existing rows rather than duplicate them
- if upload fails, local files remain intact and can be retried

### 5.4 Minimum run-level fields

The Panel-facing data model must preserve at least:

- `project_name`
- `repo_path` or equivalent project locator
- `preset`
- `source`
- `git_ref`
- `git_sha`
- `triggered_by`
- `started_at`
- `finished_at`
- `duration_sec` or equivalent total duration
- `strict_mode`
- `status`
- `block_reason`
- `modules`
- `generated_at` or run record creation time

### 5.5 Minimum module-level fields

Each module entry must preserve at least:

- `module_name`, e.g. `apps/api`
- `language` or stack label
- `commands` used for `build / lint / typecheck / test / coverage`
- `checker_results`
- `coverage_pct`
- `baseline_pct`
- `coverage_gate_pct`
- `coverage_delta_pct`
- `coverage_parser`
- `status`
- `block_reason`

### 5.6 Minimum checker result fields

Each checker result must preserve at least:

- `checker`: `build / lint / typecheck / test / coverage`
- `status`: `pass / fail / timeout / skip`
- `detail`
- `duration_sec`

## 6. Persistence Model

Week 1 uses dual-layer persistence:

- CLI local files are local artifacts
- database tables are the Panel query store

`apps/api` owns the CLI upload path into DB and the read path from DB into the Panel.

Recommended minimum tables:

### 6.1 `panel_projects`

| Field | Description |
|---|---|
| `id` | Primary key |
| `project_key` | Unique project identifier |
| `project_name` | Display name |
| `repo_path` | Project root path |
| `preset` | Project type |
| `onboarding_status` | `ready / pending / blocked / custom-needed` |
| `commands` | Optional command overrides |
| `thresholds` | Coverage tolerance, floor, lint/typecheck thresholds |
| `timeouts` | Per-check timeout settings |
| `notify` | Notification settings such as Feishu webhook |
| `created_at` | Record creation time |
| `updated_at` | Last update time |

### 6.2 `panel_runs`

| Field | Description |
|---|---|
| `id` | Primary key |
| `run_key` | Unique run identifier if generated; otherwise derive from project + git SHA + started time |
| `project_id` | Foreign key to `panel_projects.id` |
| `source` | Run source, e.g. local CLI or CI |
| `git_ref` | Branch or tag |
| `git_sha` | Commit SHA |
| `triggered_by` | Trigger user or system |
| `started_at` | Run start time |
| `finished_at` | Run finish time |
| `duration_sec` | Total execution duration |
| `status` | Aggregated project result |
| `block_reason` | Block reason, nullable |
| `strict_mode` | Whether CI-blocking mode was enabled |
| `created_at` | Record creation time |

### 6.3 `panel_modules`

| Field | Description |
|---|---|
| `id` | Primary key |
| `project_id` | Foreign key to `panel_projects.id` |
| `module_name` | Module path, e.g. `apps/api` |
| `stack` | Detected stack summary |
| `language` | Language or stack label |
| `updated_at` | Last sync time |

### 6.4 `panel_run_modules`

| Field | Description |
|---|---|
| `id` | Primary key |
| `run_id` | Foreign key to `panel_runs.id` |
| `module_id` | Foreign key to `panel_modules.id` |
| `stack` | Runtime stack summary |
| `language` | Runtime language or stack label |
| `status` | Aggregated module result for this run |
| `coverage_pct` | Current line coverage |
| `baseline_pct` | Baseline line coverage echoed in this run |
| `coverage_gate_pct` | Derived gate threshold |
| `coverage_delta_pct` | Difference vs baseline |
| `coverage_parser` | Parser used to read coverage data |
| `block_reason` | Module-specific blocking reason |
| `updated_at` | Last sync time |

### 6.5 `panel_checker_results`

| Field | Description |
|---|---|
| `id` | Primary key |
| `run_id` | Foreign key to `panel_runs.id` |
| `run_module_id` | Foreign key to `panel_run_modules.id` |
| `checker` | `build / lint / typecheck / test / coverage` |
| `status` | `pass / fail / timeout / skip` |
| `detail` | Checker detail text |
| `duration_sec` | Execution duration |
| `created_at` | Record creation time |

### 6.6 `panel_baselines`

| Field | Description |
|---|---|
| `id` | Primary key |
| `project_id` | Foreign key to `panel_projects.id` |
| `module_id` | Foreign key to `panel_modules.id` |
| `baseline_pct` | Baseline line coverage |
| `updated_at` | Baseline update time |

Requirements:

- Query performance only needs to cover Week 1 latest-status display
- Keep raw run records for audit and for `agentshield report`
- If a project has no run record yet, return `check result = not-run`, `health = unknown`
- DB sync is idempotent by `project_key`, `run_key`, `(project_id, module_name)`, `(run_id, module_id)`, and `(run_module_id, checker)` uniqueness
- Baseline data is stored separately per module and joined at read time or denormalized into run summaries
- Project detail and latest-run module cards should read per-run status fields from `panel_run_modules`
- Stable module identity and discovery metadata should read from `panel_modules`

## 7. Aggregated Response

The Panel uses a unified aggregated result for display. In Week 1, the response is read from the database query model that was written by the CLI write endpoints.

Response schema:

```json
{
  "generated_at": "2026-03-29T02:00:00Z",
  "projects": [
    {
      "project_key": "agent-shield",
      "name": "agent-shield",
      "preset": "infer-monorepo",
      "module_count": 2,
      "onboarding_status": "ready",
      "health": "failing",
      "check_all": "fail",
      "last_run_at": "2026-03-29T01:30:00Z",
      "block_reason": "apps/web coverage below gate",
      "modules": [
        {
          "module_name": "apps/api",
          "status": "pass",
          "coverage_pct": 81.2,
          "baseline_pct": 81.0,
          "coverage_gate_pct": 76.0
        },
        {
          "module_name": "apps/web",
          "status": "fail",
          "coverage_pct": 58.3,
          "baseline_pct": 72.0,
          "coverage_gate_pct": 67.0,
          "block_reason": "coverage below gate"
        }
      ]
    }
  ]
}
```

## 8. Write and Aggregation Rules

- `agentshield init` calls `POST /api/v1/panel/projects/register` after initialization completes
- `agentshield baseline update` calls `POST /api/v1/panel/baselines` after baseline data is finalized
- `agentshield check` calls `POST /api/v1/panel/runs` after run results are finalized
- The latest synchronized run is the source for project overview unless no runs exist
- Project-level `check_all` is derived from module-level results
- Module-level status is derived from checker results and coverage gate evaluation
- A failing coverage gate in any module makes that module `fail`
- In `--strict` mode, the same failure is also a blocking reason for CI
- `last_run_at` is derived from the latest synchronized `finished_at`
- `block_reason` in overview is taken from the latest synchronized run; if empty, show `—`
- `health` is derived on read, not stored as a source-of-truth field
- `baseline update` changes baseline data; upload updates `panel_baselines` and future derived values
- upload failure must not modify local files
- `report` still reads historical run files and remains the reference behavior for Week 1 history ordering

## 9. Status Definitions

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

### Checker result

- `pass`: checker completed successfully
- `fail`: checker completed and failed its rule
- `timeout`: checker exceeded timeout
- `skip`: checker intentionally not executed

### Health derivation rules

| check_all | health |
|---|---|
| `pass` | `healthy` |
| `fail` | `failing` |
| `timeout` | `warning` |
| `blocked` | `warning` |
| `not-run` | `unknown` |

## 10. Technical Constraints

- Use `apps/web` to host the Panel
- Use `apps/api` to host sync and read endpoints
- Week 1 source data is file-backed under the AgentShield runtime directory, and DB is the Panel query store
- The first supported project shape is monorepo or multi-module, not only single-project summary
- Coverage gate logic must reflect actual baseline tolerance rules from the CLI
- Week 1 delivers a read-only dashboard only

## 11. Acceptance Criteria

- PRD fields match the data actually produced by Week 1 CLI flows
- Panel can represent multiple sub-modules under one project
- Panel can display build, lint, typecheck, test, and coverage outcomes
- Panel can display current coverage, baseline, and gate threshold per module
- Panel can show the latest failing reason such as `apps/web coverage below gate`
- If no run exists yet, the project displays `not-run` and `unknown`
- Health derivation rules are correct
- Leads can view overall status without entering the CLI
- CLI write endpoints are idempotent
- DB-backed query endpoints remain consistent with the latest successfully uploaded data

## 12. One-line Definition

> Week 1 Panel uses CLI write endpoints as the primary persistence path and a database-backed query model for Panel display.
