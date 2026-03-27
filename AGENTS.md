# Source Of Truth

- `openapi/openapi.yaml`
- `docs/contracts/*`
- `apps/api/app/schemas/*`
- `docs/Ai Agent 友好型 开发指南.docx`
- `docs/AagentShield QA自动化功能 可行性调研.docx`

# Current Priority

- Phase 1: QA 自动化能力
- Phase 2: 安全类 Agent Shield 深化能力

# Rules

- monorepo only
- schema-first
- no cross-layer import
- frontend uses Next.js App Router
- backend uses FastAPI + Pydantic
- generated tests must stay under `.qa-agent/generated/`
- generated SDK must not be edited by hand
- baseline updates must be explicit and reviewable

# Required Checks

- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm check:openapi`

# Delivery Constraint

- 当前任何新增功能，默认优先服务于 QA 自动化主线。
- 安全类需求只沉淀范围说明，不进入本阶段实现。
