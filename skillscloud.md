# Skills Cloud

This file captures reusable cross-project workflows. It currently records the first AgentShield skill templates.

## qa-scope-review

- Input: requirement docs, priority, and phase boundaries
- Output: implementation scope, explicit non-goals, and acceptance criteria

## openapi-sync

- Input: FastAPI routes and Pydantic models
- Output: updated `openapi/openapi.yaml` and a contract diff summary

## qa-regression-baseline

- Input: current test results and historical baseline
- Output: regression decision, coverage delta, and baseline update eligibility

## test-style-alignment

- Input: existing project tests, Analyzer output, and coverage gaps
- Output: style-aligned test generation constraints

## planner-generator-evaluator

- Planner: define the contract, scope, and success criteria
- Generator: implement within the agreed constraints
- Evaluator: verify behavior, contracts, and tests without changing the requirement
