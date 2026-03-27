# agent-shield-monorepo

The main AgentShield workspace scaffold, standardized as a monorepo built with `Next.js + FastAPI + pnpm + uv + OpenAPI + GitHub Actions`.

The current stage focuses on a single top priority:

- `QA automation feasibility research`

The repository does not enter phase two yet:

- Security-focused AgentShield work is deferred to a later phase

## Structure

```text
apps/
  web/        Next.js App Router
  api/        FastAPI
packages/
  schemas/    Shared contract and generation notes
  sdk/        Future generated SDK output
  ui/         Future shared UI components
openapi/      OpenAPI contract
tests/        Cross-application smoke / integration tests
docs/
  contracts/  User flows, state model, and test specification
  requirements/
.github/
AGENTS.md
CLAUDE.md
skillscloud.md
```

## Project Principles

- Monorepo is a hard requirement, not an optional preference.
- FastAPI + Pydantic serve as the backend contract source.
- OpenAPI must stay in sync with the implementation.
- Quality gates must include lint, test, typecheck, and OpenAPI consistency checks.
- QA automation is Phase 1, and security-focused AgentShield work belongs to Phase 2.

## Local Setup

```bash
pnpm install
uv sync --project apps/api --extra dev
pnpm dev:web
uv run --project apps/api uvicorn app.main:app --reload
```

## Current Scaffold

- Root monorepo structure
- `AGENTS.md` / `CLAUDE.md` / `skillscloud.md`
- Minimal FastAPI API scaffold
- Minimal Next.js frontend scaffold
- Pre-commit and GitHub Actions templates
- Phase 1 QA automation contract documents

## Handoff Docs

- `docs/handoff/team-handoff.md`
- `docs/handoff/github-publish-guide.md`
