# Panel Local End-to-End Validation Runbook

This runbook is the baseline local validation flow for the Week 1 Panel write path.

It validates the three CLI-to-panel upload chains:

- `agentshield init --yes` -> `POST /api/v1/panel/projects/register`
- `agentshield baseline update` -> `POST /api/v1/panel/baselines`
- `agentshield check --strict` -> `POST /api/v1/panel/runs`

## Scope

This flow validates:

- local API is reachable
- local PostgreSQL is reachable by the API container
- CLI can call the real panel API through `AGENTSHIELD_PANEL_BASE_URL`
- project registration is persisted
- run upload is persisted
- baseline upload either persists real line coverage data or is intentionally skipped when no accurate baseline exists

This flow does not guarantee that the target repository itself passes checks.
It only validates that the upload path behaves correctly against real local services.

## Preconditions

From the workspace root:

```bash
cd /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield
docker compose ps
curl -s http://127.0.0.1:8000/healthz
```

Expected:

- `agentshield-api` is up
- `agentshield-postgres` is healthy
- `/healthz` returns `{"status":"ok", ...}`

If API code changed, rebuild it first:

```bash
docker compose up --build -d api
docker compose logs api --tail=80
```

## Environment

Set the real panel base URL before running the CLI:

```bash
export AGENTSHIELD_PANEL_BASE_URL=http://127.0.0.1:8000
unset AGENTSHIELD_PANEL_TOKEN
```

Local API currently runs without auth, so do not set a token for local validation.

## Validation Target

Use a concrete repo root. The default validated repo is:

```bash
cd /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/example-repo/infer-monorepo
```

For this repo:

- `project_key = infer-monorepo`

## Source Of Truth

For local validation, use these two sources:

- panel read API:
  - `GET /api/v1/panel/projects/{project_key}`
  - `GET /api/v1/panel/projects/{project_key}/latest`
- PostgreSQL inside the container:
  - `docker exec agentshield-postgres psql ...`

Do not rely on host-side `psql -h 127.0.0.1 -p 55432 ...` as the primary source of truth.
During local validation we observed a mismatch where host-side `psql` and the API container were not reading the same effective dataset.

## Step 0: Optional Clean State Check

Before running the flow, check whether the project already exists:

```bash
curl -s http://127.0.0.1:8000/api/v1/panel/projects/infer-monorepo
docker exec agentshield-postgres psql -U agentshield -d agentshield_panel_dev -c "select id, project_key, onboarding_status, preset from panel_projects where project_key='infer-monorepo';"
```

Expected for a clean run:

- API returns `PROJECT_NOT_FOUND`
- DB query returns `0 rows`

## Step 1: Validate `init -> register`

Run:

```bash
AGENTSHIELD_PANEL_BASE_URL='http://127.0.0.1:8000' \
uv run --project /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo/packages/cli \
agentshield init --yes
```

Expected CLI outcomes:

- `.agentshield/config.yaml` is created or refreshed
- `.qa-agent/runs/latest.json` exists
- `.agentshield/baselines/*.json` exist
- CLI prints `Panel sync: project register ok`

Expected panel outcomes:

```bash
curl -s http://127.0.0.1:8000/api/v1/panel/projects/infer-monorepo
docker exec agentshield-postgres psql -U agentshield -d agentshield_panel_dev -c "select id, project_key, onboarding_status, preset from panel_projects where project_key='infer-monorepo';"
```

Validate:

- project detail returns `200`
- `project.project_key = infer-monorepo`
- `project.preset = null`
- `project.onboarding_status` matches the real init result
- `panel_projects` contains one row for `infer-monorepo`

### Known repo-specific caveat

`infer-monorepo` may hang during `init --yes` because one generated custom check runs:

```text
make openapi-sync-check
```

If that happens:

- treat the repo as a bad target for full `init` completion
- keep the generated local artifacts
- manually validate registration with:

```bash
AGENTSHIELD_PANEL_BASE_URL='http://127.0.0.1:8000' \
/Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo/packages/cli/.venv/bin/python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
from agentshield_cli.config import load_config
from agentshield_cli.panel_sync import sync_project_register, sync_baselines
config, _, _ = load_config(Path('.agentshield/config.yaml'))
print('register_result=', sync_project_register(config, 'blocked'))
print('baselines_result=', sync_baselines(config, baseline_dir=Path('.agentshield/baselines'), updated_at=datetime.now(timezone.utc)))
PY
```

This preserves the real API/DB validation even if the repo's own generated checks are not stable.

## Step 2: Validate `baseline update -> baselines`

Inspect baseline files first:

```bash
find .agentshield/baselines -maxdepth 1 -type f -print -exec sed -n '1,220p' {} \;
```

Run:

```bash
printf 'y\n' | AGENTSHIELD_PANEL_BASE_URL='http://127.0.0.1:8000' \
uv run --project /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo/packages/cli \
agentshield baseline update
```

Expected outcomes split into two cases.

### Case A: Real line coverage baseline exists

Expected CLI output:

- `Panel sync: baselines ok`

Expected DB validation:

```bash
docker exec agentshield-postgres psql -U agentshield -d agentshield_panel_dev -c "select m.module_name, b.baseline_pct, b.updated_at from panel_modules m join panel_baselines b on b.module_id = m.id where m.project_id = (select id from panel_projects where project_key='infer-monorepo') order by m.module_name;"
```

Validate:

- at least one `baseline_pct` is non-null
- uploaded values match local baseline `thresholds.line`

### Case B: No real line coverage baseline exists

Expected CLI output:

- `Panel sync: baselines skipped (no coverage baseline data)`

This is valid behavior.
It means the CLI correctly refused to upload guessed baseline values.

## Step 3: Validate `check -> runs`

Run:

```bash
AGENTSHIELD_PANEL_BASE_URL='http://127.0.0.1:8000' \
uv run --project /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo/packages/cli \
agentshield check --strict
```

Expected CLI outcomes:

- `.qa-agent/runs/latest.json` is updated
- CLI prints `Panel sync: run ok`
- command may exit `1` if the repo fails checks; that is acceptable for this validation

Expected API validation:

```bash
curl -s http://127.0.0.1:8000/api/v1/panel/projects/infer-monorepo/latest
curl -s http://127.0.0.1:8000/api/v1/panel/projects/infer-monorepo
```

Validate:

- `/latest` returns `200`
- `run.run_key` matches the latest local `.qa-agent/runs/*.json` filename
- `run.status` matches the actual CLI run result
- `modules[]` is populated
- each module contains `checker_results[]`

Expected DB validation:

```bash
docker exec agentshield-postgres psql -U agentshield -d agentshield_panel_dev -c "select id, run_key, status, finished_at from panel_runs where project_id=(select id from panel_projects where project_key='infer-monorepo') order by id desc limit 5; select count(*) as run_modules from panel_run_modules where run_id=(select id from panel_runs where project_id=(select id from panel_projects where project_key='infer-monorepo') order by id desc limit 1); select count(*) as checker_results from panel_checker_results where run_id=(select id from panel_runs where project_id=(select id from panel_projects where project_key='infer-monorepo') order by id desc limit 1);"
```

Validate:

- newest `panel_runs.run_key` matches the API `/latest` payload
- `panel_run_modules` count is greater than `0`
- `panel_checker_results` count is greater than `0`

## Negative Check: `--dry-run` Must Not Upload Runs

Run:

```bash
AGENTSHIELD_PANEL_BASE_URL='http://127.0.0.1:8000' \
uv run --project /Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo/packages/cli \
agentshield check --dry-run
```

Validate:

- CLI does not print `Panel sync: run ok`
- latest `panel_runs` row does not change

## Pass Criteria

Local end-to-end validation is considered passed when all of these are true:

- API health is green
- project registration is visible through panel read API and container-side PostgreSQL
- baseline update either uploads real `line` coverage baselines or explicitly skips because there is no accurate baseline
- check upload produces a new `panel_runs` row plus `panel_run_modules` and `panel_checker_results`

## Current Known Behavior On `infer-monorepo`

As of `2026-03-30`:

- `init` registration path is valid
- `baseline update` may skip upload because local baseline files contain no `thresholds.line`
- `check --strict` upload path is valid even when the repo itself fails many checks
- generated module set may expand after later scans, so `run_modules` can exceed the module count first registered during `init`

## Recommended Repeatable Order

For every future local validation, use this exact order:

1. `docker compose ps`
2. `curl -s http://127.0.0.1:8000/healthz`
3. optional clean-state check for the target project
4. `agentshield init --yes`
5. verify project row through API + container-side PostgreSQL
6. `agentshield baseline update`
7. verify baseline upload or intentional skip
8. `agentshield check --strict`
9. verify `/latest` plus `panel_runs`, `panel_run_modules`, and `panel_checker_results`

This document is the default baseline procedure unless the local runtime topology changes.
