# AgentShield

AgentShield is a multi-project QA automation platform. It scans your codebase, runs quality checks (build, lint, type check, unit tests, coverage), and blocks merges when quality drops.

**Phase 1 goal:** Connect 10+ internal projects to a unified quality gate within one month.

**Phase 2 (future):** Security-focused Agent capabilities.

---

## How It Works

```
Developer pushes code
        ↓
agentshield check          ← runs in CI or locally
        ↓
AI scans project structure ← detects language, framework, test commands
        ↓
Executes checks            ← build / lint / typecheck / test / coverage
        ↓
Compares against baseline  ← blocks if coverage drops more than threshold
        ↓
Sends notification         ← Feishu / Slack on failure
```

---

## Repository Structure

```text
apps/
  api/              FastAPI backend — API endpoints and schemas
  web/              Next.js frontend — results dashboard (Phase 2)
packages/
  cli/              agentshield CLI tool (Week 1 deliverable)
  schemas/          Shared Pydantic / TypeScript contract types
  sdk/              Auto-generated SDK — do not edit by hand
  ui/               Shared UI components (Phase 2)
openapi/
  openapi.yaml      API contract — source of truth for all endpoints
docs/
  prd/              Product requirements
  design/           Technical design documents and CLI command spec
  contracts/        User flow, state model, test specification
  requirements/     Phase-scoped requirement boundaries
  handoff/          Onboarding guides for new team members
tests/
  smoke/            Cross-application smoke tests
.github/
  workflows/ci.yml  CI quality gate
AGENTS.md           Rules every AI agent and developer must follow
CLAUDE.md           Project-specific override rules for Claude
skillscloud.md      Reusable workflow templates
```

---

## Prerequisites

Make sure you have these installed:

| Tool | Version | Purpose |
|---|---|---|
| Node.js | 22+ | Frontend |
| pnpm | 10.11.0 | Node package manager |
| Python | 3.11+ | Backend |
| uv | latest | Python package manager |

Check your setup:

```bash
node --version
pnpm --version
python3 --version
uv --version
```

---

## Local Development Setup

**1. Clone the repository**

```bash
git clone https://github.com/tomo-inc/agent-shield-monorepo.git
cd agent-shield-monorepo
```

**2. Install Node dependencies**

```bash
pnpm install
```

**3. Install Python dependencies**

```bash
uv sync --project apps/api --extra dev
```

**4. Start the backend**

```bash
uv run --project apps/api uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

API docs available at: http://localhost:8000/docs

**5. Start the frontend**

```bash
pnpm dev:web
```

Frontend runs at: http://localhost:3000

---

## Available Commands

```bash
# Run all quality checks (lint + typecheck + test + openapi sync check)
pnpm run ci

# Individual checks
pnpm lint           # ESLint (web) + Ruff (api)
pnpm typecheck      # TypeScript + Pyright
pnpm test           # Vitest (web) + pytest (api)
pnpm check:openapi  # Verify openapi.yaml matches current code

# Development
pnpm dev:web        # Start Next.js dev server
pnpm build:web      # Build frontend
```

---

## Key Rules

These rules apply to all contributors — human and AI:

- **Schema-first**: every API change must update `openapi/openapi.yaml` first, then the code
- **No cross-layer imports**: frontend does not import from backend code directly
- **Generated files are read-only**: never edit `packages/sdk/` by hand
- **Baseline updates require explicit confirmation**: coverage baselines cannot be auto-overwritten
- **Generated tests stay in `.qa-agent/generated/`**: never write them into application test directories
- **Phase 1 only**: all new work defaults to the QA automation track — security features are documented only, not implemented

---

## CI Quality Gate

Every push and pull request runs the following checks automatically:

```
pnpm lint           must pass
pnpm typecheck      must pass
pnpm test           must pass
pnpm check:openapi  openapi.yaml must match the code
```

A failing check blocks the merge.

## Commit Discipline

Do not treat the first failing command as the whole problem.

- Fixes must be validated against the full affected quality gate before commit.
- API schema or route changes must re-run `pnpm check:openapi` and update `openapi/openapi.yaml` if the generated contract changes.
- Package-local fixes are not enough when the change crosses package boundaries. In that case, prefer root commands such as `pnpm typecheck`, `pnpm test`, or `pnpm ci`.
- Before commit, run `git status --short` and verify that generated or derived files are not left stale.

---

## Project Documents

| Document | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Rules for AI agents and developers |
| [docs/prd/AgentShield PRD.docx](docs/prd/AgentShield%20PRD.docx) | Product requirements |
| [docs/design/AgentShield Complete Technical Solution Week1.docx](docs/design/AgentShield%20Complete%20Technical%20Solution%20Week1.docx) | Week 1 technical plan |
| [docs/design/AgentShield CLI Command Design Documentation.docx](docs/design/AgentShield%20CLI%20Command%20Design%20Documentation.docx) | CLI command design |
| [docs/contracts/user-flow.md](docs/contracts/user-flow.md) | QA automation flow |
| [docs/contracts/test-spec.md](docs/contracts/test-spec.md) | Test case requirements |
| [docs/handoff/team-handoff.md](docs/handoff/team-handoff.md) | Onboarding guide |

---

## Recommended Reading Order for New Members

1. This file
2. `AGENTS.md` — do not skip this
3. `docs/requirements/qa-automation-scope.md`
4. `docs/contracts/user-flow.md`
5. `docs/design/AgentShield Complete Technical Solution Week1.docx`

---

## Branch Strategy

### Branch Roles

| Branch | Purpose |
|---|---|
| `main` | Production-ready. Clean linear history. Never push directly. Every commit represents one complete, reviewed delivery unit. |
| `dev` | Integration branch. All feature and fix branches merge here first for combined CI validation before going to `main`. |
| `feat/xxx` | New feature. Branched from `main`. |
| `fix/xxx` | Bug fix. Branched from `main`. |
| `hotfix/xxx` | Urgent production fix. Branched from `main`, merged to `main` first, then synced to `dev`. |

### Workflow

```
main
 │
 ├── feat/payment-checker      (branched from main)
 │        │
 │        │  squash merge
 │        ▼
 │       dev  ← integration validation, CI must pass here first
 │        │
 │        │  PR + squash merge (one commit per feat/fix)
 │        ▼
 └──── main  ← clean history, one commit = one complete feature or fix
```

### Rules

- **Always branch from `main`**, not from `dev`
- **Squash merge into `dev`** — keeps dev history readable
- **Squash merge into `main` via PR** — each feat/fix raises its own PR to `main` after passing `dev` validation
- **Never push directly to `main`** — all changes go through a PR
- **Hotfix goes to `main` first**, then cherry-pick or merge into `dev`

### Commit Message Conventions

| Prefix | When to use |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `hotfix:` | Urgent production fix |
| `chore:` | Tooling, config, dependency updates |
| `docs:` | Documentation only |
| `refactor:` | Code restructure with no behaviour change |

---

## Current Status

| Area | Status |
|---|---|
| Monorepo structure | Done |
| FastAPI skeleton | Done |
| Next.js skeleton | Done |
| CI quality gate | Done |
| OpenAPI contract | Done |
| agentshield CLI | In progress — Week 1 |
| AI Analyzer | In progress — Week 1 |
| Baseline management | Planned — Week 2 |
| MCP interface | Planned — Week 3 |
| Dashboard | Planned — Phase 2 |
