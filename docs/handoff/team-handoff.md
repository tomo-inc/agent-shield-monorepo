# AgentShield Project Handoff

## What This Is

This is the main repository for `AgentShield`, named `agent-shield-monorepo`.

This is not a complete product yet. It is the first-version engineering template, intended to establish a unified development structure, Agent rules, foundational code skeleton, and CI templates to support future team collaboration.

## Current Phase

Phase 1 only:

- QA automation capabilities

Phase 2 is not in scope:

- Security-focused AgentShield deep capabilities

All current design and code should serve the QA automation track. Security modules are not to be implemented at this stage.

## Why This Structure

The project follows the AI Agent-Friendly Development Guide. Core requirements:

- Must use monorepo
- Frontend uses Next.js App Router
- Backend uses FastAPI + Pydantic
- Contracts managed via OpenAPI
- Must include `AGENTS.md`, `CLAUDE.md`, `skillscloud.md`
- Must have pre-commit and CI quality gates

## What Is Already Done

- Monorepo directory structure is in place
- Frontend `apps/web` has a minimal page skeleton
- Backend `apps/api` has a minimal FastAPI endpoint skeleton
- OpenAPI file is at `openapi/openapi.yaml`
- Agent rule files are complete
- QA automation contract documents are complete
- GitHub Actions CI template is created
- pre-commit template is created

## Directory Overview

```text
apps/
  web/                  Next.js frontend
  api/                  FastAPI backend
packages/
  schemas/              Shared contract types
  sdk/                  Future generated SDK location
  ui/                   Future shared UI components
openapi/
  openapi.yaml          API contract file
docs/
  contracts/            User flow, state model, test spec
  requirements/         Phase-scoped requirements
  handoff/              Handoff documents
.github/workflows/
  ci.yml                CI template
AGENTS.md               System-level rules
CLAUDE.md               Project-specific override rules
skillscloud.md          Reusable workflow templates
```

## Recommended Reading Order

New team members should read in this order:

1. `README.md`
2. `AGENTS.md`
3. `docs/requirements/qa-automation-scope.md`
4. `docs/contracts/user-flow.md`
5. `docs/contracts/db-state-model.md`
6. `docs/contracts/test-spec.md`

For background on the original research inputs:

- `docs/Ai Agent 友好型 开发指南.docx`
- `docs/AagentShield QA自动化功能 可行性调研.docx`

## Current State

This repository is a handoff-ready engineering framework, not a fully operational business system.

What is clearly defined:

- Project structure
- Tech stack direction
- Phase priorities
- Agent rules
- CI approach
- First-order QA automation contracts

What is not yet complete:

- Actual business module implementation
- Full implementation of Analyzer / Generator / Runner / Tracker
- Dependency installation and lockfile finalization
- End-to-end CI pipeline validation

## Collaboration Guidelines

- Do not skip `AGENTS.md` before writing code
- New features should default to the QA automation track
- Any API change must be synced to `openapi/openapi.yaml`
- Important changes should be documented in contracts first
- Security requirements are to be recorded only, not implemented

## Recommended Starting Points

Good areas to work on in parallel:

- Refine QA automation requirements
- Design API contracts for Analyzer / Generator / Runner / Tracker
- Improve the frontend display page
- Add API endpoints and tests
- Set up local development and CI dependencies
