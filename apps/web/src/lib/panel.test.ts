import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getPanelProject, getPanelProjects } from "./panel";

type MockJsonResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function response(status: number, data: unknown): MockJsonResponse {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  };
}

describe("panel api client", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("loads panel projects with default base url", async () => {
    vi.mocked(fetch).mockResolvedValue(
      response(200, {
        generated_at: "2026-03-31T07:00:00Z",
        projects: [
          {
            project_key: "demo-project",
            project_name: "Demo Project",
            preset: "infer-monorepo",
            module_count: 2,
            onboarding_status: "ready",
            health: "healthy",
            check_all: "pass",
            last_run_at: "2026-03-31T07:00:00Z",
            block_reason: null,
            coverage_avg_pct: 91.2,
          },
        ],
      }),
    );

    const result = await getPanelProjects();

    expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8088/api/v1/panel/projects", { cache: "no-store" });
    expect(result).toEqual({
      generated_at: "2026-03-31T07:00:00Z",
      projects: [
        {
          project_key: "demo-project",
          project_name: "Demo Project",
          repo_path: "demo-project",
          preset: "infer-monorepo",
          onboarding_status: "ready",
          module_count: 2,
          health: "healthy",
          source: null,
          triggered_by: null,
          status: "pass",
          block_reason: null,
          coverage_avg_pct: 91.2,
          started_at: null,
          finished_at: "2026-03-31T07:00:00Z",
          duration_sec: null,
        },
      ],
    });
  });

  it("uses PANEL_API_BASE_URL override", async () => {
    vi.stubEnv("PANEL_API_BASE_URL", "http://panel-api.internal");
    vi.mocked(fetch).mockResolvedValue(response(200, { generated_at: "now", projects: [] }));

    await getPanelProjects();

    expect(fetch).toHaveBeenCalledWith("http://panel-api.internal/api/v1/panel/projects", { cache: "no-store" });
  });

  it("throws when loading project list fails", async () => {
    vi.mocked(fetch).mockResolvedValue(response(503, { message: "unavailable" }));

    await expect(getPanelProjects()).rejects.toThrow("Failed to load panel projects: 503");
  });

  it("returns null when project detail is missing", async () => {
    vi.mocked(fetch).mockResolvedValue(response(404, {}));

    await expect(getPanelProject("missing")).resolves.toBeNull();
  });

  it("throws when project detail request fails", async () => {
    vi.mocked(fetch).mockResolvedValue(response(500, {}));

    await expect(getPanelProject("broken")).rejects.toThrow("Failed to load panel project 'broken': 500");
  });

  it("maps project detail with latest run data", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response(200, {
          generated_at: "2026-03-31T08:00:00Z",
          project: {
            project_key: "demo-project",
            project_name: "Demo Project",
            preset: "infer-monorepo",
            onboarding_status: "ready",
            latest_run: {
              run_key: "demo-run-ref",
              status: "pass",
              block_reason: null,
              finished_at: "2026-03-31T07:59:00Z",
            },
            modules: [
              {
                module_name: "apps/api",
                stack: "Python / FastAPI",
                language: "Python",
                status: "pass",
                coverage_pct: 90,
                baseline_pct: 88,
                coverage_gate_pct: 80,
                coverage_delta_pct: 2,
                coverage_parser: "pytest-cov-json",
                block_reason: null,
                checker_results: [],
              },
            ],
          },
        }),
      )
      .mockResolvedValueOnce(
        response(200, {
          generated_at: "2026-03-31T08:00:01Z",
          run: {
            run_key: "demo-run",
            source: "local-cli",
            git_ref: "main",
            git_sha: "abc123",
            triggered_by: "dawei",
            started_at: "2026-03-31T07:58:00Z",
            finished_at: "2026-03-31T07:59:00Z",
            duration_sec: 60,
            strict_mode: true,
            status: "pass",
            block_reason: null,
            modules: [
              {
                module_name: "apps/web",
                stack: "TypeScript / Next.js",
                language: "TypeScript",
                status: "fail",
                coverage_pct: 72.4,
                baseline_pct: 70,
                coverage_gate_pct: 68,
                coverage_delta_pct: 2.4,
                coverage_parser: "istanbul-json",
                block_reason: "coverage low",
                checker_results: [
                  { checker: "build", status: "pass", detail: "ok", duration_sec: 1 },
                ],
              },
            ],
          },
        }),
      );

    const result = await getPanelProject("demo-project");

    expect(fetch).toHaveBeenNthCalledWith(1, "http://127.0.0.1:8088/api/v1/panel/projects/demo-project", { cache: "no-store" });
    expect(fetch).toHaveBeenNthCalledWith(2, "http://127.0.0.1:8088/api/v1/panel/projects/demo-project/latest", { cache: "no-store" });
    expect(result).toEqual({
      generated_at: "2026-03-31T08:00:00Z",
      project: {
        project_key: "demo-project",
        project_name: "Demo Project",
        repo_path: "demo-project",
        preset: "infer-monorepo",
        onboarding_status: "ready",
        latest_run: {
          run_key: "demo-run",
          source: "local-cli",
          git_ref: "main",
          git_sha: "abc123",
          triggered_by: "dawei",
          started_at: "2026-03-31T07:58:00Z",
          finished_at: "2026-03-31T07:59:00Z",
          duration_sec: 60,
          strict_mode: true,
          status: "pass",
          block_reason: null,
        },
        modules: [
          {
            module_name: "apps/web",
            stack: "TypeScript / Next.js",
            language: "TypeScript",
            status: "fail",
            coverage_pct: 72.4,
            baseline_pct: 70,
            coverage_gate_pct: 68,
            coverage_delta_pct: 2.4,
            coverage_parser: "istanbul-json",
            block_reason: "coverage low",
            checker_results: [{ checker: "build", status: "pass", detail: "ok", duration_sec: 1 }],
          },
        ],
      },
    });
  });

  it("falls back to detail data when latest run is not found", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response(200, {
          generated_at: "2026-03-31T08:00:00Z",
          project: {
            project_key: "fallback-project",
            project_name: "Fallback Project",
            preset: "infer-monorepo",
            onboarding_status: "pending",
            latest_run: {
              run_key: "fallback-ref",
              status: "blocked",
              block_reason: "awaiting setup",
              finished_at: "2026-03-31T07:59:00Z",
            },
            modules: [
              {
                module_name: "sdk/python",
                stack: null,
                language: null,
                status: "blocked",
                coverage_pct: null,
                baseline_pct: null,
                coverage_gate_pct: null,
                coverage_delta_pct: null,
                coverage_parser: null,
                block_reason: null,
                checker_results: [],
              },
            ],
          },
        }),
      )
      .mockResolvedValueOnce(response(404, {}));

    const result = await getPanelProject("fallback-project");

    expect(result?.project.latest_run).toEqual({
      run_key: "fallback-ref",
      source: null,
      git_ref: null,
      git_sha: null,
      triggered_by: null,
      started_at: null,
      finished_at: "2026-03-31T07:59:00Z",
      duration_sec: null,
      strict_mode: false,
      status: "blocked",
      block_reason: "awaiting setup",
    });
    expect(result?.project.modules).toEqual([
      {
        module_name: "sdk/python",
        stack: null,
        language: null,
        status: "blocked",
        coverage_pct: null,
        baseline_pct: null,
        coverage_gate_pct: null,
        coverage_delta_pct: null,
        coverage_parser: null,
        block_reason: null,
        checker_results: [],
      },
    ]);
  });

  it("creates a not-run fallback when project has no latest run ref", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response(200, {
          generated_at: "2026-03-31T08:00:00Z",
          project: {
            project_key: "never-run",
            project_name: "Never Run",
            preset: "infer-monorepo",
            onboarding_status: "custom-needed",
            latest_run: null,
            modules: [],
          },
        }),
      )
      .mockResolvedValueOnce(response(404, {}));

    const result = await getPanelProject("never-run");

    expect(result?.project.latest_run).toEqual({
      run_key: "never-run-latest",
      source: null,
      git_ref: null,
      git_sha: null,
      triggered_by: null,
      started_at: null,
      finished_at: null,
      duration_sec: null,
      strict_mode: false,
      status: "not-run",
      block_reason: null,
    });
  });

  it("throws when latest run request fails", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        response(200, {
          generated_at: "2026-03-31T08:00:00Z",
          project: {
            project_key: "demo-project",
            project_name: "Demo Project",
            preset: "infer-monorepo",
            onboarding_status: "ready",
            latest_run: null,
            modules: [],
          },
        }),
      )
      .mockResolvedValueOnce(response(502, {}));

    await expect(getPanelProject("demo-project")).rejects.toThrow("Failed to load latest panel run for 'demo-project': 502");
  });
});
