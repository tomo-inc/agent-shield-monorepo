# Week 1 最小后台 Panel 需求定义

> 版本：v6.0
> 日期：2026-03-29
> 阶段：Month 1 / Week 1

## 1. 目标

Week 1 交付一个最小后台 Panel，供负责人查看项目接入状态、最近一次检测结果和阻塞原因。

## 2. 范围

### 必做

- `apps/web` 提供可访问的 Panel 页面
- `apps/api` 提供最小结果上传与查询接口
- 支持本地 CLI 和 CI 上传检测结果
- 页面展示项目总览、健康度、最近一次 `check-all` 结果、最近运行时间、阻塞原因

### 不做

- smoke 展示
- 数据库
- 登录与权限系统
- 手动触发执行
- 项目配置编辑
- 历史趋势
- 复杂筛选和搜索

## 3. 数据流

```text
CLI / CI
  ↓
POST /api/v1/panel/runs
  ↓
apps/api 落盘并聚合
  ↓
GET /api/v1/panel/projects
  ↓
apps/web Panel 展示
```

## 4. 页面需求

### 页面 1：项目状态总览页

字段如下：

| 字段 | 说明 |
|---|---|
| 项目名称 | 项目标识 |
| preset | 项目类型，如 `infer-monorepo`、`java-maven`、`custom` |
| 接入状态 | `ready / pending / blocked / custom-needed` |
| 健康度 | `healthy / warning / failing / unknown` |
| check-all | `pass / fail / timeout / blocked / not-run` |
| 最近运行时间 | 最近一次结果更新时间 |
| 阻塞原因 | 无阻塞显示 `—` |

页面要求：

- 默认加载一次数据
- 提供手动刷新按钮
- 表格展示
- 状态与健康度有颜色区分

## 5. API 需求

### 5.1 上传接口

`POST /api/v1/panel/runs`

用途：

- 本地 CLI 或 CI 上传一次检测结果

最小字段：

- `org`
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

要求：

- 上传失败不阻断 CLI 主流程
- 上传失败必须输出 warning 或日志

### 5.2 查询接口

`GET /api/v1/panel/projects`

用途：

- 返回 Panel 项目总览列表

`GET /api/v1/panel/projects/{project}/latest`

用途：

- 返回单项目最近一次结果

## 6. 聚合数据

Panel 展示使用统一聚合结果。

建议路径：

- `.qa-agent/status/projects_status.json`

也可以由 `apps/api` 直接返回同结构数据。

Schema：

```json
{
  "generated_at": "2026-03-29T02:00:00Z",
  "projects": [
    {
      "org": "tomo-inc",
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

## 7. 状态定义

### 接入状态

- `ready`：已接入，可执行
- `pending`：已登记，未完成接入
- `blocked`：存在外部阻塞
- `custom-needed`：需要定制适配

### check-all

- `pass`：通过
- `fail`：失败
- `timeout`：超时
- `blocked`：阻塞
- `not-run`：未运行

### 健康度规则

| check_all | health |
|---|---|
| `pass` | `healthy` |
| `fail` | `failing` |
| `timeout` | `warning` |
| `blocked` | `warning` |
| `not-run` | `unknown` |

## 8. 技术约束

- 使用 `apps/web` 承载 Panel
- 使用 `apps/api` 承载上传与查询接口
- 不引入数据库
- 结果以文件落盘和聚合为主
- Week 1 只做只读看板

## 9. 验收标准

- 浏览器可访问 Panel 页面
- 本地 CLI 结果可上传
- CI 结果可上传
- 页面可展示全部已登记项目
- 页面字段与聚合结果一致
- 健康度推导规则正确
- 负责人无需进入 CLI 即可查看总体状态

## 10. 一句话定义

> Week 1 交付一个最小只读后台 Panel，并补齐 CLI / CI 结果上传接口。
