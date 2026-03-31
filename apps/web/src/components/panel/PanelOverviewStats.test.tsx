import React from "react";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { PanelProject } from "@/src/lib/panel";

import { PanelOverviewStats } from "./PanelOverviewStats";

function project(overrides: Partial<PanelProject>): PanelProject {
  return {
    project_key: "project-key",
    project_name: "Project Name",
    repo_path: "project-key",
    preset: "infer-monorepo",
    onboarding_status: "ready",
    module_count: 1,
    health: "healthy",
    source: null,
    triggered_by: null,
    status: "pass",
    block_reason: null,
    coverage_avg_pct: 90,
    started_at: null,
    finished_at: null,
    duration_sec: null,
    ...overrides,
  };
}

describe("PanelOverviewStats", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("renders zero values for an empty project list", () => {
    render(<PanelOverviewStats projects={[]} />);

    expect(screen.getByText("Total Projects")).toBeTruthy();
    expect(screen.getByText("0 modules in scope")).toBeTruthy();
    expect(screen.getByText("0% of total")).toBeTruthy();
    expect(screen.getByText("Needs attention")).toBeTruthy();
  });

  it("aggregates healthy, failing, and blocked projects", () => {
    render(
      <PanelOverviewStats
        projects={[
          project({ project_key: "healthy", module_count: 2, health: "healthy", status: "pass" }),
          project({ project_key: "warning-health", module_count: 3, health: "warning", status: "pass" }),
          project({ project_key: "blocked-status", module_count: 4, health: "unknown", status: "blocked" }),
          project({ project_key: "failing", module_count: 5, health: "failing", status: "fail" }),
        ]}
      />,
    );

    expect(screen.getByText("14 modules in scope")).toBeTruthy();
    expect(screen.getByText("25% of total")).toBeTruthy();
    expect(screen.getByText("Tests or checks failing")).toBeTruthy();
  });
});
