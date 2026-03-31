import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PanelProject } from "@/src/lib/panel";

import { PanelProjectCard } from "./PanelProjectCard";

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

describe("PanelProjectCard", () => {
  it("renders project details without block reason", () => {
    render(<PanelProjectCard project={project({})} />);

    expect(screen.getByText("Agent Shield")).toBeTruthy();
    expect(screen.getByText("View detail")).toBeTruthy();
    expect(screen.getByText("-")).toBeTruthy();
  });

  it("renders block reason and different tones", () => {
    render(
      <>
        <PanelProjectCard project={project({ project_key: "p1", onboarding_status: "pending", health: "warning", status: "blocked", block_reason: "Awaiting approval" })} />
        <PanelProjectCard project={project({ project_key: "p2", onboarding_status: "blocked", health: "failing", status: "fail", block_reason: "Tests failing" })} />
        <PanelProjectCard project={project({ project_key: "p3", onboarding_status: "custom-needed", health: "unknown", status: null, block_reason: null })} />
      </>,
    );

    expect(screen.getByText("Awaiting approval")).toBeTruthy();
    expect(screen.getByText("Tests failing")).toBeTruthy();
    expect(screen.getAllByText("-").length).toBeGreaterThan(0);
  });
});
