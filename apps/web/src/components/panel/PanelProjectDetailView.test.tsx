import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PanelProjectDetail } from "@/src/lib/panel";

import { PanelProjectDetailView } from "./PanelProjectDetailView";

function project(overrides: Partial<PanelProjectDetail>): PanelProjectDetail {
  return {
    project_key: "agent-shield",
    project_name: "Agent Shield",
    repo_path: "agent-shield",
    preset: "infer-monorepo",
    onboarding_status: "ready",
    latest_run: {
      run_key: "run-1",
      source: "local-cli",
      git_ref: "main",
      git_sha: "abc123",
      triggered_by: "dawei",
      started_at: "2026-03-31T06:00:00Z",
      finished_at: "2026-03-31T06:01:00Z",
      duration_sec: 60,
      strict_mode: true,
      status: "pass",
      block_reason: null,
    },
    modules: [
      {
        module_name: "apps/api",
        stack: "Python / FastAPI",
        language: "Python",
        status: "pass",
        coverage_pct: 81,
        baseline_pct: 80,
        coverage_gate_pct: 76,
        coverage_delta_pct: 1,
        coverage_parser: "pytest-cov-json",
        block_reason: null,
        checker_results: [
          { checker: "build", status: "pass", detail: "ok", duration_sec: 1 },
          { checker: "lint", status: "fail", detail: "error", duration_sec: 1 },
        ],
      },
      {
        module_name: "apps/web",
        stack: null,
        language: null,
        status: "blocked",
        coverage_pct: 59,
        baseline_pct: 70,
        coverage_gate_pct: 67,
        coverage_delta_pct: -11,
        coverage_parser: "istanbul-json",
        block_reason: "coverage below gate",
        checker_results: [
          { checker: "typecheck", status: "timeout", detail: null, duration_sec: null },
          { checker: "coverage", status: "skip", detail: null, duration_sec: null },
        ],
      },
    ],
    ...overrides,
  };
}

describe("PanelProjectDetailView", () => {
  it("renders detail stats and module rows", () => {
    render(<PanelProjectDetailView generatedAt="2026-03-31T06:20:22Z" project={project({})} />);

    expect(screen.getByText("Return to home")).toBeTruthy();
    expect(screen.getByText("Average module coverage")).toBeTruthy();
    expect(screen.getByText("1 module(s) blocked")).toBeTruthy();
    expect(screen.getByText("coverage below gate")).toBeTruthy();
    expect(screen.getByText("-")).toBeTruthy();
    expect(screen.getByText("70.0%")).toBeTruthy();
  });

  it("renders no baseline values and no blocked module note when clean", () => {
    render(
      <PanelProjectDetailView
        generatedAt="2026-03-31T06:20:22Z"
        project={project({
          latest_run: {
            run_key: "run-2",
            source: null,
            git_ref: null,
            git_sha: null,
            triggered_by: null,
            started_at: null,
            finished_at: null,
            duration_sec: null,
            strict_mode: false,
            status: "fail",
            block_reason: "tests failed",
          },
          modules: [
            {
              module_name: "sdk/python",
              stack: "Python / SDK",
              language: null,
              status: "fail",
              coverage_pct: null,
              baseline_pct: null,
              coverage_gate_pct: null,
              coverage_delta_pct: null,
              coverage_parser: null,
              block_reason: null,
              checker_results: [{ checker: "test", status: "pass", detail: null, duration_sec: null }],
            },
          ],
        })}
      />,
    );

    expect(screen.getByText("No blocking reasons reported")).toBeTruthy();
    expect(screen.getByText("Finished -")).toBeTruthy();
    expect(screen.getAllByText("-").length).toBeGreaterThan(0);
  });
});
