# 第 1 周最小化管理面板 PRD

> 版本：v7.3
> 日期：2026-03-30
> 阶段：第 1 个月 / 第 1 周

## 1. 目标

在第 1 周交付一个最小可用的管理面板，使负责人能够查看项目接入状态、最近一次检查结果以及任何阻塞原因。

## 2. 范围

### 必须交付

- 本 PRD 必须反映 Week 1 阶段由 CLI 流程实际产出的数据
- Panel 数据模型必须兼容 `agentshield check`、`agentshield init --yes`、`agentshield baseline update` 和 `agentshield report`
- 页面展示：项目总览、最近一次运行结果、模块级汇总、coverage gate 结果、最近运行时间和阻塞原因
- Week 1 的数据来源为 CLI 生成的配置文件、运行历史文件和 baseline 文件
- `apps/api` 提供 CLI 写接口和 Panel 读接口，并将数据落库作为 Panel 查询存储

### 不在本期范围内

- Smoke test 展示
- 登录与权限系统
- 手动触发执行
- 项目配置编辑
- 历史趋势
- 复杂筛选与搜索
- 替换 CLI 文件产物作为 Week 1 的原始事实来源

## 3. 数据流

```text
agentshield init / baseline update / check
  ↓
CLI 写本地 `.agentshield/*` 文件
  ↓
CLI 调用 apps/api 写接口
  + POST /api/v1/panel/projects/register
  + POST /api/v1/panel/baselines
  + POST /api/v1/panel/runs
  ↓
apps/api 校验并写入数据库
  ↓
apps/web Panel 展示
```

## 4. 页面需求

### 页面 1：项目状态总览

字段：

| 字段 | 说明 |
|---|---|
| 项目名称 | 来自配置文件的项目标识 |
| preset | 项目类型，例如 `infer-monorepo`、`java-maven`、`custom` |
| 模块数量 | 检测到的子模块数量，例如 `apps/api`、`apps/web` |
| 接入状态 | 基于 Week 1 实际状态推导：`ready / pending / blocked / custom-needed` |
| 健康状态 | 基于最近一次聚合检查结果推导：`healthy / warning / failing / unknown` |
| check 结果 | 最近一次项目级聚合结果：`pass / fail / timeout / blocked / not-run` |
| 最近运行时间 | 最近一次结果更新时间戳 |
| Coverage 摘要 | 在可用时展示当前行覆盖率与 gate 阈值 |
| 阻塞原因 | 若无阻塞则显示 `—` |

每个项目展开后的详细信息应展示：

- 子模块名称，例如 `apps/api`、`apps/web`
- 检测到的技术栈摘要，例如 `Python / FastAPI`、`TypeScript / Next.js`
- `build`、`lint`、`typecheck`、`test`、`coverage` 的检查结果
- coverage 解析器类型（如可用），例如 `pytest-cov-json`、`istanbul-json`、`jacoco-xml`
- 每个模块的 baseline 对比结果
- 最近一次运行因 gate 失败而触发的 strict 模式阻塞原因

页面要求：

- 页面挂载后加载一次数据
- 提供手动刷新按钮
- 使用表格布局
- 状态列和健康状态列使用颜色区分

## 5. Week 1 数据契约

Week 1 不以数据库记录作为原始事实来源。CLI 本地产物仍然存在，但 Panel 侧通过 CLI 调用 API 直接落库，数据库作为 Panel 查询存储。

在本 PRD 中，`.agentshield/` 是 Week 1 用于配置、运行记录和 baseline 的规范运行时目录命名。

### 5.1 源文件

- `.agentshield/config.yaml`
- `.agentshield/runs/*.json`
- `.agentshield/baselines/*.json`

每类文件的最小语义如下：

- `config.yaml`：项目标识、preset、命令覆盖、阈值、超时、通知设置
- `runs/*.json`：一条完整运行记录，包含模块级检查结果和项目级聚合结果
- `baselines/*.json`：模块级 baseline 覆盖率，用于推导 coverage gate

### 5.2 CLI 写接口

Week 1 需要 3 类 CLI 写接口：

- `POST /api/v1/panel/projects/register`
  用于项目初始化完成后上传项目配置和模块列表
- `POST /api/v1/panel/baselines`
  用于首次 baseline 采集或 `baseline update` 后上传 baseline
- `POST /api/v1/panel/runs`
  用于每次 `agentshield check` 完成后上传运行结果

调用时机：

- `projects/register`：`config.yaml` 成功写入后调用
- `baselines`：baseline 文件成功写入后调用
- `runs`：本次 run 文件成功写入后调用

要求：

- 写接口失败不能阻塞 CLI 主流程
- CLI 需要输出 warning 或日志
- 重复上传必须幂等

### 5.3 数据库存储目标

Panel 层必须将 CLI 通过 API 上传的数据持久化为数据库查询模型。

要求：

- 数据库是 Panel 的查询存储
- 写入过程必须幂等
- 重复上传必须更新已有记录，而不是产生重复数据
- 上传失败时，本地文件保持不变，可重试

### 5.4 运行级最小字段

面向 Panel 的数据模型至少要保留：

- `project_name`
- `repo_path` 或等价的项目定位字段
- `preset`
- `source`
- `git_ref`
- `git_sha`
- `triggered_by`
- `started_at`
- `finished_at`
- `duration_sec` 或等价的总耗时
- `strict_mode`
- `status`
- `block_reason`
- `modules`
- `generated_at` 或运行记录创建时间

### 5.5 模块级最小字段

每个模块条目至少要保留：

- `module_name`，例如 `apps/api`
- `language` 或技术栈标签
- `commands`，用于 `build / lint / typecheck / test / coverage`
- `checker_results`
- `coverage_pct`
- `baseline_pct`
- `coverage_gate_pct`
- `coverage_delta_pct`
- `coverage_parser`
- `status`
- `block_reason`

### 5.6 Checker 结果最小字段

每个 checker 结果至少要保留：

- `checker`：`build / lint / typecheck / test / coverage`
- `status`：`pass / fail / timeout / skip`
- `detail`
- `duration_sec`

## 6. 持久化模型

Week 1 使用双层持久化：

- CLI 本地文件是本地产物
- 数据库表是 Panel 查询存储

`apps/api` 负责接收 CLI 上传、写入数据库，并负责 Panel 的查询读取。

建议的最小表结构：

### 6.1 `panel_projects`

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `project_key` | 唯一项目标识 |
| `project_name` | 展示名称 |
| `repo_path` | 项目根路径 |
| `preset` | 项目类型 |
| `onboarding_status` | `ready / pending / blocked / custom-needed` |
| `commands` | 可选的命令覆盖 |
| `thresholds` | Coverage 容忍度、floor、lint/typecheck 阈值 |
| `timeouts` | 各检查项超时设置 |
| `notify` | 通知配置，例如 Feishu Webhook |
| `created_at` | 创建时间 |
| `updated_at` | 最后更新时间 |

### 6.2 `panel_runs`

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `run_key` | 若有则为唯一运行标识；否则可由 project + git SHA + started time 推导 |
| `project_id` | 指向 `panel_projects.id` 的外键 |
| `source` | 运行来源，例如本地 CLI 或 CI |
| `git_ref` | 分支或标签 |
| `git_sha` | Commit SHA |
| `triggered_by` | 触发用户或系统 |
| `started_at` | 运行开始时间 |
| `finished_at` | 运行结束时间 |
| `status` | 项目级聚合结果 |
| `modules` | 模块结果对象数组 |
| `block_reason` | 阻塞原因，可为空 |
| `strict_mode` | 是否启用了 CI 阻塞模式 |
| `created_at` | 记录创建时间 |

### 6.3 `panel_modules`

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `project_id` | 指向 `panel_projects.id` 的外键 |
| `module_name` | 模块路径，例如 `apps/api` |
| `stack` | 检测到的技术栈摘要 |
| `language` | 语言或技术栈标签 |
| `status` | 模块级聚合结果 |
| `coverage_pct` | 当前行覆盖率 |
| `baseline_pct` | baseline 行覆盖率 |
| `coverage_gate_pct` | 推导出的 gate 阈值 |
| `coverage_delta_pct` | 相比 baseline 的差值 |
| `coverage_parser` | 用于解析 coverage 数据的解析器 |
| `block_reason` | 模块级阻塞原因 |
| `updated_at` | 最后同步时间 |

### 6.4 `panel_checker_results`

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `run_id` | 指向 `panel_runs.id` 的外键 |
| `module_id` | 指向 `panel_modules.id` 的外键 |
| `checker` | `build / lint / typecheck / test / coverage` |
| `status` | `pass / fail / timeout / skip` |
| `detail` | Checker 详情 |
| `duration_sec` | 执行耗时 |
| `created_at` | 创建时间 |

### 6.5 `panel_baselines`

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `project_id` | 指向 `panel_projects.id` 的外键 |
| `module_id` | 指向 `panel_modules.id` 的外键 |
| `baseline_pct` | Baseline 行覆盖率 |
| `updated_at` | Baseline 更新时间 |

要求：

- 查询性能只需覆盖 Week 1 的最新状态展示需求
- 保留原始运行记录，以支持审计和 `agentshield report`
- 若项目尚无运行记录，则返回 `check result = not-run`、`health = unknown`
- 数据库同步以 `project_key`、`run_key` 和 `(project_id, module_name, checker, run_id)` 唯一性实现幂等
- baseline 数据按模块单独存储，并在读取时关联，或在运行摘要中做冗余展开

## 7. 聚合响应

Panel 使用统一的聚合结果进行展示。在 Week 1 中，响应从数据库查询模型中读取，该查询模型由 CLI 通过写接口写入。

响应结构：

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

## 8. 写入与聚合规则

- `agentshield init` 在项目初始化完成后调用 `POST /api/v1/panel/projects/register`
- `agentshield baseline update` 在 baseline 成功更新后调用 `POST /api/v1/panel/baselines`
- `agentshield check` 在本次 run 结果生成后调用 `POST /api/v1/panel/runs`
- 除非项目尚无运行记录，否则项目总览以最近一次已同步运行作为数据来源
- 项目级 `check_all` 由模块级结果聚合得出
- 模块级状态由 checker 结果和 coverage gate 计算结果共同推导
- 任一模块 coverage gate 失败，则该模块结果为 `fail`
- 在 `--strict` 模式下，同样的失败也会成为 CI 的阻塞原因
- `last_run_at` 取自最近一次已同步的 `finished_at`
- 总览中的 `block_reason` 取自最近一次已同步运行；若为空则显示 `—`
- `health` 在读取时推导，不作为事实来源字段存储
- `baseline update` 会更新 baseline 数据；上传后更新 `panel_baselines` 以及后续派生值
- 上传失败不能修改本地源文件
- `report` 仍从历史运行文件中读取数据，是 Week 1 历史排序行为的参考实现

## 9. 状态定义

### 接入状态

- `ready`：已接入，可执行
- `pending`：已登记，但接入未完成
- `blocked`：存在外部阻塞
- `custom-needed`：需要定制化适配

### Check 结果

- `pass`：通过
- `fail`：失败
- `timeout`：超时
- `blocked`：被阻塞
- `not-run`：尚未运行

### Checker 结果

- `pass`：checker 成功执行并通过
- `fail`：checker 执行完成，但未通过规则校验
- `timeout`：checker 执行超时
- `skip`：checker 被有意跳过

### 健康状态推导规则

| check_all | health |
|---|---|
| `pass` | `healthy` |
| `fail` | `failing` |
| `timeout` | `warning` |
| `blocked` | `warning` |
| `not-run` | `unknown` |

## 10. 技术约束

- 使用 `apps/web` 承载 Panel
- 使用 `apps/api` 承载同步与查询接口
- Week 1 的源数据位于 AgentShield 运行时目录下，数据库作为 Panel 查询存储
- 第一批支持的项目形态是 monorepo 或多模块项目，而不仅是单项目汇总
- Coverage gate 逻辑必须反映 CLI 中真实的 baseline 容忍度规则
- 第 1 周仅交付只读仪表盘

## 11. 验收标准

- PRD 中定义的字段与 Week 1 CLI 实际产出的数据一致
- Panel 能表达一个项目下的多个子模块
- Panel 能展示 build、lint、typecheck、test 和 coverage 的结果
- Panel 能展示每个模块的当前覆盖率、baseline 和 gate 阈值
- Panel 能展示类似 `apps/web coverage below gate` 的最近失败原因
- 如果还没有运行记录，项目显示 `not-run` 和 `unknown`
- 健康状态推导规则正确
- 负责人无需进入 CLI 即可查看整体状态
- CLI 写接口具备幂等性
- 基于数据库的查询结果与最新一次成功上传的数据保持一致

## 12. 一句话定义

> Week 1 Panel 以 CLI 写接口落库为主路径，并以数据库查询模型支撑 Panel 展示。
