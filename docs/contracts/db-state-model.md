# QA Automation State Model

## Core Entities

### `pipeline_runs`

- `run_id`
- `requested_by`
- `source_ref`
- `status`
- `created_at`
- `completed_at`

### `test_targets`

- `target_id`
- `run_id`
- `file_path`
- `language`
- `framework`
- `risk_level`
- `coverage_gap`

### `baseline_snapshots`

- `baseline_id`
- `scope_ref`
- `result_hash`
- `coverage_percent`
- `updated_by`
- `updated_at`

## Invariants

- `completed` => `completed_at != null`
- `regressed` => at least one historically passing item in the baseline failed in the current run
- baseline must not be overwritten automatically
- generated artifacts may only be written to `.qa-agent/generated/`
- compare results for the same `run_id` must be replayable
