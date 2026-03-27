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
- `regressed` => baseline 中至少一个历史通过项本次失败
- baseline 不能自动覆盖
- 生成物只能写入 `.qa-agent/generated/`
- 同一 `run_id` 的 compare 结果必须可重放
