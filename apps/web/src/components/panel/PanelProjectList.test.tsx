import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PanelProject } from "@/src/lib/panel";

import { PanelProjectList } from "./PanelProjectList";

function project(overrides: Partial<PanelProject>): PanelProject {
  return {
    project_key: "agent-shield",
    project_name: "Agent Shield",
    repo_path: "agent-shield",
    preset: "infer-monorepo",
    onboarding_status: "ready",
    module_count: 2,
    health: "healthy",
    source: null,
    triggered_by: null,
    status: "pass",
    block_reason: null,
    coverage_avg_pct: 88.8,
    started_at: null,
    finished_at: null,
    duration_sec: null,
    ...overrides,
  };
}

describe("PanelProjectList", () => {
  it("renders empty state", () => {
    render(<PanelProjectList projects={[]} />);

    expect(screen.getByText("No data")).toBeTruthy();
  });

  it("renders project rows with coverage and block fallbacks", () => {
    render(
      <PanelProjectList
        projects={[
          project({ project_key: "p1", coverage_avg_pct: 88.8, block_reason: "Coverage below gate" }),
          project({ project_key: "p2", health: "unknown", status: null, coverage_avg_pct: null, block_reason: null }),
        ]}
      />,
    );

    expect(screen.getByText("Coverage below gate")).toBeTruthy();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.getByText("88.8%")).toBeTruthy();
  });
});
