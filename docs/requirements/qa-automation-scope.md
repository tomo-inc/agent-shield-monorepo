# QA Automation — Phase 1 Scope

## Reference Sources

- `docs/Ai Agent 友好型 开发指南.docx`
- `docs/AagentShield QA自动化功能 可行性调研.docx`

## Goal

Transform testing from a manual, isolated activity into an automated capability that can be invoked directly by developers, CI pipelines, and upstream Agents.

## Problems to Solve

- Low test coverage with high cost to fill manually
- Unclear regression boundaries leading to missed tests
- No self-verification signal for AI Agents after code changes
- Inconsistent test styles increasing maintenance cost
- Long test preparation cycles before new feature releases
- Coverage numbers look acceptable but critical paths remain untested

## Phase 1 Modules

- `Analyzer`: code recognition, coverage gap identification, boundary condition inference
- `Generator`: test generation using few-shot examples aligned to project style
- `Runner`: unified multi-framework test execution with normalized output
- `Tracker`: baseline management and regression detection

## Out of Scope

- Security-focused AgentShield deep capabilities
- IDE plugin for end users
- Heavy-UI E2E automation platform

## Initial Deliverables

- Monorepo template
- Quality gate template
- OpenAPI contract
- QA automation contract documents
- API and frontend skeleton
