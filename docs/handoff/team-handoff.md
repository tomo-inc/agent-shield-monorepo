# AgentShield 项目框架交接说明

## 这是什么

这是 `AgentShield` 的主仓库框架，仓库目录名为 `agent-shield-monorepo`。

当前不是完整产品，而是第一版工程模板，目的是先把项目的统一开发结构、Agent 规则、基础代码骨架和 CI 模板搭起来，方便后续多人协作。

## 当前阶段

当前只做 Phase 1：

- QA 自动化能力

当前不做 Phase 2：

- 安全类 Agent Shield 深化能力

也就是说，现阶段所有设计和代码都优先服务于 QA 自动化，不进入安全模块实现。

## 为什么要用这个结构

项目结构遵循《AI Agent 友好型开发指南》，核心要求是：

- 必须使用 monorepo
- 前端统一用 Next.js App Router
- 后端统一用 FastAPI + Pydantic
- 契约统一通过 OpenAPI 管理
- 必须有 `AGENTS.md`、`CLAUDE.md`、`skillscloud.md`
- 必须有 pre-commit 和 CI 质量门禁

## 当前已经完成的内容

- Monorepo 目录结构已经搭好
- 前端 `apps/web` 已有最小页面骨架
- 后端 `apps/api` 已有 FastAPI 最小接口骨架
- OpenAPI 文件已经落在 `openapi/openapi.yaml`
- Agent 规则文件已经补齐
- QA 自动化的契约文档已经补齐
- GitHub Actions CI 模板已经创建
- pre-commit 模板已经创建

## 当前目录说明

```text
apps/
  web/                  Next.js 前端
  api/                  FastAPI 后端
packages/
  schemas/              共享契约说明
  sdk/                  未来生成 SDK 的位置
  ui/                   未来共享 UI 组件的位置
openapi/
  openapi.yaml          API 契约文件
docs/
  contracts/            用户流程、状态模型、测试规范
  requirements/         分阶段需求说明
  handoff/              交接文档
.github/workflows/
  ci.yml                CI 模板
AGENTS.md               系统级规则
CLAUDE.md               项目特殊补丁规则
skillscloud.md          可复用流程说明
```

## 必看文档

组员进入项目后，建议先按这个顺序看：

1. `README.md`
2. `AGENTS.md`
3. `docs/requirements/qa-automation-scope.md`
4. `docs/contracts/user-flow.md`
5. `docs/contracts/db-state-model.md`
6. `docs/contracts/test-spec.md`

如果要了解项目最初的输入材料，再看：

- `docs/Ai Agent 友好型 开发指南.docx`
- `docs/AagentShield QA自动化功能 可行性调研.docx`

## 目前的真实状态

这份仓库现在是“可交接的工程框架”，不是“已经能完整运行的业务系统”。

目前已经明确的部分：

- 项目结构
- 技术栈方向
- 阶段优先级
- Agent 规则
- CI 思路
- QA 自动化的一阶契约

目前还没有完全做完的部分：

- 真正的业务模块实现
- Analyzer / Generator / Runner / Tracker 的完整落地
- 依赖安装和 lockfile 固化
- CI 全链路跑通

## 协作建议

- 不要跳过 `AGENTS.md` 直接写代码
- 新功能默认优先贴近 QA 自动化主线
- 任何 API 变更都要同步改 `openapi/openapi.yaml`
- 任何重要改动都优先补文档和契约
- 安全类需求暂时只记录，不直接进入开发

## 组员现在最适合接手什么

比较适合并行推进的内容：

- 继续细化 QA 自动化需求
- 设计 Analyzer / Generator / Runner / Tracker 的 API contract
- 完善前端展示页面
- 补充 API 端点和测试
- 补充本地开发和 CI 所需依赖
