# Panel Projects Contract

## Endpoints

- `GET /api/v1/panel/projects`
- `GET /api/v1/panel/projects/{project_key}`
- `GET /api/v1/panel/projects/{project_key}/latest`

## List response

```json
{
  "generated_at": "2026-03-30T10:00:35Z",
  "projects": [
    {
      "project_key": "agent-shield-monorepo",
      "project_name": "AgentShield Monorepo",
      "repo_path": "/workspace/agent-shield-monorepo",
      "preset": "infer-monorepo",
      "onboarding_status": "ready",
      "module_count": 2,
      "health": "failing",
      "source": "local-cli",
      "triggered_by": "dawei",
      "status": "fail",
      "block_reason": "apps/web coverage below gate",
      "started_at": "2026-03-30T10:00:00Z",
      "finished_at": "2026-03-30T10:00:31Z",
      "duration_sec": 31.0
    }
  ]
}
```

## List field mapping

- `project_key`: from `panel_projects.project_key`
- `project_name`: from `panel_projects.project_name`
- `repo_path`: from `panel_projects.repo_path`
- `preset`: from `panel_projects.preset`
- `onboarding_status`: from `panel_projects.onboarding_status`
- `module_count`: derived from associated `panel_modules` count
- `health`: derived from latest `panel_runs.status`
- `source`: from latest `panel_runs.source`
- `triggered_by`: from latest `panel_runs.triggered_by`
- `status`: from latest `panel_runs.status`
- `block_reason`: from latest `panel_runs.block_reason`
- `started_at`: from latest `panel_runs.started_at`
- `finished_at`: from latest `panel_runs.finished_at`
- `duration_sec`: from latest `panel_runs.duration_sec`

## Health derivation

- `pass -> healthy`
- `fail -> failing`
- `timeout -> warning`
- `blocked -> warning`
- `not-run -> unknown`

## Project detail response

```json
{
  "generated_at": "2026-03-30T10:00:35Z",
  "project": {
    "project_key": "agent-shield-monorepo",
    "project_name": "AgentShield Monorepo",
    "repo_path": "/workspace/agent-shield-monorepo",
    "preset": "infer-monorepo",
    "onboarding_status": "ready",
    "latest_run": {
      "run_key": "agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
      "source": "local-cli",
      "git_ref": "main",
      "git_sha": "abc123",
      "triggered_by": "dawei",
      "started_at": "2026-03-30T10:00:00Z",
      "finished_at": "2026-03-30T10:00:31Z",
      "duration_sec": 31.0,
      "strict_mode": true,
      "status": "fail",
      "block_reason": "apps/web coverage below gate"
    },
    "modules": [
      {
        "module_name": "apps/api",
        "stack": "Python / FastAPI",
        "language": "Python",
        "status": "pass",
        "coverage_pct": 81.2,
        "baseline_pct": 81.0,
        "coverage_gate_pct": 76.0,
        "coverage_delta_pct": 0.2,
        "coverage_parser": "pytest-cov-json",
        "block_reason": null,
        "checker_results": [
          {
            "checker": "build",
            "status": "pass",
            "detail": "",
            "duration_sec": 3.2
          }
        ]
      }
    ]
  }
}
```

## Detail field mapping

- `project.project_key`: from `panel_projects.project_key`
- `project.project_name`: from `panel_projects.project_name`
- `project.repo_path`: from `panel_projects.repo_path`
- `project.preset`: from `panel_projects.preset`
- `project.onboarding_status`: from `panel_projects.onboarding_status`
- `project.latest_run.*`: from latest `panel_runs`
- `project.modules[]`: from `panel_modules`
- `project.modules[].checker_results[]`: from latest run `panel_checker_results`
- `project.modules[].baseline_pct`: current effective baseline reflected from `panel_baselines`

## Latest run response

```json
{
  "generated_at": "2026-03-30T10:00:35Z",
  "project_key": "agent-shield-monorepo",
  "source": "local-cli",
  "triggered_by": "dawei",
  "status": "fail",
  "block_reason": "apps/web coverage below gate",
  "started_at": "2026-03-30T10:00:00Z",
  "finished_at": "2026-03-30T10:00:31Z",
  "duration_sec": 31.0
}
```

## Latest run field mapping

- `project_key`: from `panel_projects.project_key`
- remaining fields: from latest `panel_runs`

## Current implementation note

- `panel_projects`, `panel_runs`, `panel_modules`, `panel_checker_results`, and `panel_baselines` are not created yet.
- `apps/api` currently returns stable mock aggregated project detail data from the service layer.
- `GET /api/v1/panel/projects` overview items are derived from the mock detail payloads.
- `generated_at` is generated at request time in UTC ISO 8601 format.

## Invariants

- `generated_at` must always be a UTC ISO 8601 string.
- `projects` must always be present and must be an array.
- List response must always include `preset`, `module_count`, and `health`.
- `project` detail response must contain exactly one project record.
- `project.latest_run` must always be present in the current mock detail response.
- `project.modules` must always be present and must be an array.
- `project.modules[].checker_results` must always be present and must be an array.
- Latest run response only exposes run-derived fields plus `project_key`.
- Unknown `project_key` returns `404`.
