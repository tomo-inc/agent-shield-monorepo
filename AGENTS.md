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

# Pre-Commit Validation Rule

- Do not stop at the failing check reported by CI or local output.
- Every code change must be validated against the full affected quality gate before commit.
- Changes under `apps/api/app/schemas/*`, API routes, or request/response models must also run `pnpm check:openapi` and regenerate `openapi/openapi.yaml` when needed.
- Changes under `packages/cli/*` must run the relevant CLI typecheck or tests, and any cross-package change should prefer root commands over partial package-only checks.
- If the impact crosses package or layer boundaries, run the root validation set instead of only the local leaf command.
- Before commit, run `git status --short` and verify no generated or derived file that should be updated is left behind.
- A fix is not complete until the relevant validation command passes locally.

# Delivery Constraint

- Any new work should default to the QA automation track.
- Security-oriented requirements stay documented only and do not enter implementation in this phase.
