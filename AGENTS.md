# Source Of Truth

- `openapi/openapi.yaml`
- `docs/contracts/*`
- `apps/api/app/schemas/*`
- `docs/requirements/qa-automation-scope.md`
- `docs/requirements/security-phase-two.md`

# Current Priority

- Phase 1: QA automation
- Phase 2: security-focused AgentShield capabilities

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

- Any new work should default to the QA automation track.
- Security-oriented requirements stay documented only and do not enter implementation in this phase.
