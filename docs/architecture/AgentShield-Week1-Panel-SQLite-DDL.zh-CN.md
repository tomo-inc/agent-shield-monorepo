# AgentShield Week 1 Panel SQLite DDL

> 版本：v1.0
> 日期：2026-03-30
> 范围：Week 1 Panel SQLite Schema

## 1. 设计说明

- SQLite 作为 Week 1 Panel 查询存储
- 所有 `json` 配置字段先以 `TEXT` 方式存储
- 所有时间字段使用 `TEXT` 存 ISO 8601 UTC
- 所有百分比使用 `REAL`
- 所有幂等性依赖唯一索引保证

## 2. DDL

```sql
CREATE TABLE IF NOT EXISTS panel_projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_key TEXT NOT NULL,
  project_name TEXT NOT NULL,
  repo_path TEXT NOT NULL,
  preset TEXT NOT NULL,
  onboarding_status TEXT NOT NULL,
  commands_json TEXT,
  thresholds_json TEXT,
  timeouts_json TEXT,
  notify_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_projects_project_key
  ON panel_projects(project_key);

CREATE TABLE IF NOT EXISTS panel_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  run_key TEXT NOT NULL,
  source TEXT,
  git_ref TEXT,
  git_sha TEXT,
  triggered_by TEXT,
  started_at TEXT,
  finished_at TEXT,
  duration_sec REAL,
  strict_mode INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  block_reason TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES panel_projects(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_runs_run_key
  ON panel_runs(run_key);

CREATE INDEX IF NOT EXISTS idx_panel_runs_project_finished_at
  ON panel_runs(project_id, finished_at DESC);

CREATE TABLE IF NOT EXISTS panel_modules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  module_name TEXT NOT NULL,
  stack TEXT,
  language TEXT,
  status TEXT NOT NULL,
  coverage_pct REAL,
  baseline_pct REAL,
  coverage_gate_pct REAL,
  coverage_delta_pct REAL,
  coverage_parser TEXT,
  block_reason TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES panel_projects(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_modules_project_module
  ON panel_modules(project_id, module_name);

CREATE TABLE IF NOT EXISTS panel_checker_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  module_id INTEGER NOT NULL,
  checker TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  duration_sec REAL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES panel_runs(id),
  FOREIGN KEY (module_id) REFERENCES panel_modules(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_checker_results_unique
  ON panel_checker_results(run_id, module_id, checker);

CREATE INDEX IF NOT EXISTS idx_panel_checker_results_run_id
  ON panel_checker_results(run_id);

CREATE TABLE IF NOT EXISTS panel_baselines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  module_id INTEGER NOT NULL,
  baseline_pct REAL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES panel_projects(id),
  FOREIGN KEY (module_id) REFERENCES panel_modules(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_panel_baselines_project_module
  ON panel_baselines(project_id, module_id);
```

## 3. 迁移顺序

建议 migration 顺序：

1. `panel_projects`
2. `panel_runs`
3. `panel_modules`
4. `panel_checker_results`
5. `panel_baselines`
6. 索引

## 4. Upsert 建议

### 4.1 `panel_projects`

按 `project_key` upsert。

### 4.2 `panel_runs`

按 `run_key` upsert。

### 4.3 `panel_modules`

按 `(project_id, module_name)` upsert。

### 4.4 `panel_checker_results`

按 `(run_id, module_id, checker)` upsert。

### 4.5 `panel_baselines`

按 `(project_id, module_id)` upsert。
