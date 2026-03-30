# AgentShield Week 1 Panel API Schema

> 版本：v1.0
> 日期：2026-03-30
> 范围：Week 1 Panel API

## 1. 接口清单

写接口：

- `POST /api/v1/panel/projects/register`
- `POST /api/v1/panel/baselines`
- `POST /api/v1/panel/runs`

读接口：

- `GET /api/v1/panel/projects`
- `GET /api/v1/panel/projects/{project_key}`
- `GET /api/v1/panel/projects/{project_key}/latest`

## 2. 通用约定

- 所有时间使用 ISO 8601 UTC，例如 `2026-03-30T10:00:00Z`
- 所有百分比字段使用数值类型，如 `81.2`
- 所有写接口必须幂等
- 写接口失败不能要求 CLI 回滚本地 `.agentshield/*` 文件

## 3. 写接口

## 3.1 `POST /api/v1/panel/projects/register`

用途：

- 上传项目初始化完成后的配置和模块列表

请求体：

```json
{
  "project_key": "infer-monorepo",
  "project_name": "infer-monorepo",
  "repo_path": ".",
  "preset": "infer-monorepo",
  "onboarding_status": "ready",
  "commands": {
    "build": "pnpm build",
    "lint": "pnpm lint",
    "typecheck": "pnpm typecheck",
    "test": "pnpm test",
    "coverage": "pnpm test --coverage"
  },
  "thresholds": {
    "coverage_tolerance_pct": 5,
    "coverage_floor_pct": 0,
    "lint_max_errors": 0,
    "typecheck_max_errors": 0
  },
  "timeouts": {
    "build": 300,
    "test": 600
  },
  "notify": {
    "feishu_webhook": "https://example.com/webhook"
  },
  "modules": [
    {
      "module_name": "apps/api",
      "stack": "Python / FastAPI",
      "language": "Python"
    },
    {
      "module_name": "apps/web",
      "stack": "TypeScript / Next.js",
      "language": "TypeScript"
    }
  ]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `project_key` | 是 | 项目唯一标识 |
| `project_name` | 是 | 项目展示名 |
| `repo_path` | 是 | 仓库路径 |
| `preset` | 是 | CLI 识别的 preset |
| `onboarding_status` | 是 | `ready / pending / blocked / custom-needed` |
| `commands` | 否 | 项目级命令配置 |
| `thresholds` | 否 | 阈值配置 |
| `timeouts` | 否 | timeout 配置 |
| `notify` | 否 | 通知配置 |
| `modules[]` | 是 | 模块列表 |
| `modules[].module_name` | 是 | 模块名 |
| `modules[].stack` | 否 | 技术栈文本 |
| `modules[].language` | 否 | 主语言 |

响应：

```json
{
  "ok": true,
  "project_id": 1,
  "module_count": 2
}
```

幂等规则：

- 按 `project_key` upsert `panel_projects`
- 按 `(project_id, module_name)` upsert `panel_modules`

## 3.2 `POST /api/v1/panel/baselines`

用途：

- 上传 baseline 结果

请求体：

```json
{
  "project_key": "infer-monorepo",
  "updated_at": "2026-03-30T10:00:00Z",
  "modules": [
    {
      "module_name": "apps/api",
      "baseline_pct": 81.0
    },
    {
      "module_name": "apps/web",
      "baseline_pct": 72.0
    }
  ]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `project_key` | 是 | 项目标识 |
| `updated_at` | 是 | baseline 更新时间 |
| `modules[]` | 是 | baseline 模块列表 |
| `modules[].module_name` | 是 | 模块名 |
| `modules[].baseline_pct` | 是 | baseline 行覆盖率 |

响应：

```json
{
  "ok": true,
  "project_id": 1,
  "baselines_upserted": 2
}
```

幂等规则：

- 按 `(project_id, module_id)` upsert `panel_baselines`
- 同时更新 `panel_modules.baseline_pct`

## 3.3 `POST /api/v1/panel/runs`

用途：

- 上传每次 check 的完整结果

请求体：

```json
{
  "project_key": "infer-monorepo",
  "run_key": "infer-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
  "source": "local-cli",
  "git_ref": "main",
  "git_sha": "abc123",
  "triggered_by": "alice",
  "started_at": "2026-03-30T10:00:00Z",
  "finished_at": "2026-03-30T10:00:31Z",
  "duration_sec": 31.2,
  "strict_mode": true,
  "status": "fail",
  "block_reason": "apps/web coverage below gate",
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
        { "checker": "build", "status": "pass", "detail": "", "duration_sec": 3.2 },
        { "checker": "lint", "status": "pass", "detail": "", "duration_sec": 2.1 },
        { "checker": "typecheck", "status": "pass", "detail": "", "duration_sec": 4.5 },
        { "checker": "test", "status": "pass", "detail": "86 passed / 0 failed", "duration_sec": 10.0 },
        { "checker": "coverage", "status": "pass", "detail": "Line 81.2%, gate >= 76.0%", "duration_sec": 1.0 }
      ]
    }
  ]
}
```

顶层字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `project_key` | 是 | 项目标识 |
| `run_key` | 是 | 运行唯一键 |
| `source` | 否 | 来源 |
| `git_ref` | 否 | 分支或 tag |
| `git_sha` | 否 | commit SHA |
| `triggered_by` | 否 | 触发者 |
| `started_at` | 否 | 开始时间 |
| `finished_at` | 否 | 结束时间 |
| `duration_sec` | 否 | 总耗时 |
| `strict_mode` | 是 | 是否 strict |
| `status` | 是 | 项目级状态 |
| `block_reason` | 否 | 项目级阻塞原因 |
| `modules[]` | 是 | 模块结果列表 |

模块字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `module_name` | 是 | 模块名 |
| `stack` | 否 | 技术栈文本 |
| `language` | 否 | 主语言 |
| `status` | 是 | 模块状态 |
| `coverage_pct` | 否 | 当前 coverage |
| `baseline_pct` | 否 | baseline |
| `coverage_gate_pct` | 否 | gate |
| `coverage_delta_pct` | 否 | delta |
| `coverage_parser` | 否 | coverage parser |
| `block_reason` | 否 | 模块阻塞原因 |
| `checker_results[]` | 是 | checker 明细 |

checker 字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `checker` | 是 | `build / lint / typecheck / test / coverage` |
| `status` | 是 | `pass / fail / timeout / skip` |
| `detail` | 否 | checker 输出摘要 |
| `duration_sec` | 否 | checker 耗时 |

响应：

```json
{
  "ok": true,
  "project_id": 1,
  "run_id": 10,
  "modules_upserted": 2,
  "checker_results_upserted": 10
}
```

幂等规则：

- 按 `run_key` upsert `panel_runs`
- 按 `(project_id, module_name)` upsert `panel_modules`
- 按 `(run_id, module_id, checker)` upsert `panel_checker_results`

## 4. 读接口

## 4.1 `GET /api/v1/panel/projects`

用途：

- 首页总览

响应：

```json
{
  "generated_at": "2026-03-30T10:05:00Z",
  "projects": [
    {
      "project_key": "infer-monorepo",
      "project_name": "infer-monorepo",
      "preset": "infer-monorepo",
      "module_count": 2,
      "onboarding_status": "ready",
      "health": "failing",
      "check_all": "fail",
      "last_run_at": "2026-03-30T10:00:31Z",
      "block_reason": "apps/web coverage below gate"
    }
  ]
}
```

## 4.2 `GET /api/v1/panel/projects/{project_key}`

用途：

- 项目详情

响应：

```json
{
  "generated_at": "2026-03-30T10:05:00Z",
  "project": {
    "project_key": "infer-monorepo",
    "project_name": "infer-monorepo",
    "preset": "infer-monorepo",
    "onboarding_status": "ready",
    "latest_run": {
      "run_key": "infer-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
      "status": "fail",
      "block_reason": "apps/web coverage below gate",
      "finished_at": "2026-03-30T10:00:31Z"
    },
    "modules": []
  }
}
```

## 4.3 `GET /api/v1/panel/projects/{project_key}/latest`

用途：

- 最近一次运行详情

## 5. 错误响应

建议格式：

```json
{
  "ok": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "project infer-monorepo not found"
  }
}
```

常见错误码：

- `VALIDATION_ERROR`
- `PROJECT_NOT_FOUND`
- `MODULE_NOT_FOUND`
- `RUN_NOT_FOUND`
- `INTERNAL_ERROR`
