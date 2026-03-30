# Panel API Contract

## Scope

This document defines the Week 1 Panel API contract that must stay aligned with:

- `openapi/openapi.yaml`
- `apps/api/app/schemas/panel.py`
- `docs/architecture/AgentShield-Week1-Panel-*.md`

## Implementation Rules

- backend implementation is FastAPI + Pydantic
- API evolution is schema-first
- request and response payloads must be idempotent where documented
- Week 1 storage is a query model, not the original CLI source of truth

## Endpoints

### Write APIs

- `POST /api/v1/panel/projects/register`
- `POST /api/v1/panel/baselines`
- `POST /api/v1/panel/runs`

### Read APIs

- `GET /api/v1/panel/projects`
- `GET /api/v1/panel/projects/{project_key}`
- `GET /api/v1/panel/projects/{project_key}/latest`

## Core Modeling Rules

- `panel_modules` stores stable module identity and metadata
- `panel_run_modules` stores per-run module snapshots
- `panel_checker_results` references `run_module_id`
- `panel_baselines` is the source of truth for current baseline values
- `panel_runs` stores project-level run state only

## Idempotency Keys

- project registration: `project_key`
- baseline upload: `(project_id, module_id)`
- run upload: `run_key`
- run modules: `(run_id, module_id)`
- checker results: `(run_module_id, checker)`
