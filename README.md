# agent-shield-monorepo

AgentShield 的主仓库模板，按照《Ai Agent 友好型 开发指南》统一为 `Next.js + FastAPI + pnpm + uv + OpenAPI + GitHub Actions` 的 monorepo 结构。

当前阶段只聚焦第一优先级：

- `QA 自动化功能可行性调研`

暂不进入第二阶段：

- `AgentShield 调研详细内容` 对应的安全类能力建设

## 目录

```text
apps/
  web/        Next.js App Router
  api/        FastAPI
packages/
  schemas/    契约与代码生成说明
  sdk/        未来生成 SDK 的位置
  ui/         未来共享 UI 组件的位置
openapi/      OpenAPI 契约
tests/        跨应用 smoke / integration tests
docs/
  contracts/  用户流程、状态模型、测试规范
  requirements/
.github/
AGENTS.md
CLAUDE.md
skillscloud.md
```

## 当前项目原则

- Monorepo 是前提，不拆多仓库。
- FastAPI + Pydantic 负责后端契约源。
- OpenAPI 与代码必须同步。
- 质量门禁必须包含 lint、test、typecheck、openapi consistency。
- QA 自动化是 Phase 1，安全类 Agent Shield 研究是 Phase 2。

## 本地启动

```bash
pnpm install
uv sync --project apps/api --extra dev
pnpm dev:web
uv run --project apps/api uvicorn app.main:app --reload
```

## 当前已落地内容

- 根级 monorepo 结构
- `AGENTS.md` / `CLAUDE.md` / `skillscloud.md`
- FastAPI 最小 API 骨架
- Next.js 最小前端骨架
- Pre-commit 与 GitHub Actions 模板
- QA 自动化 Phase 1 契约文档

## 交接文档

- `docs/handoff/team-handoff.md`
- `docs/handoff/github-publish-guide.md`
