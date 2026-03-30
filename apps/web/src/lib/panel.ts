export type PanelOnboardingStatus = "ready" | "pending" | "blocked" | "custom-needed";
export type PanelRunStatus = "pass" | "fail" | "timeout" | "blocked" | "not-run" | null;
export type PanelHealth = "healthy" | "warning" | "failing" | "unknown";

export type PanelProject = {
  project_key: string;
  project_name: string;
  repo_path: string;
  preset: string;
  onboarding_status: PanelOnboardingStatus;
  module_count: number;
  health: PanelHealth;
  source: string | null;
  triggered_by: string | null;
  status: PanelRunStatus;
  block_reason: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_sec: number | null;
};

export type PanelProjectsResponse = {
  generated_at: string;
  projects: PanelProject[];
};

export type PanelCheckerResult = {
  checker: "build" | "lint" | "typecheck" | "test" | "coverage";
  status: "pass" | "fail" | "timeout" | "skip";
  detail: string | null;
  duration_sec: number | null;
};

export type PanelModule = {
  module_name: string;
  stack: string | null;
  language: string | null;
  status: Exclude<PanelRunStatus, null>;
  coverage_pct: number | null;
  baseline_pct: number | null;
  coverage_gate_pct: number | null;
  coverage_delta_pct: number | null;
  coverage_parser: string | null;
  block_reason: string | null;
  checker_results: PanelCheckerResult[];
};

export type PanelLatestRun = {
  run_key: string;
  source: string | null;
  git_ref: string | null;
  git_sha: string | null;
  triggered_by: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_sec: number | null;
  strict_mode: boolean;
  status: Exclude<PanelRunStatus, null>;
  block_reason: string | null;
};

export type PanelProjectDetail = {
  project_key: string;
  project_name: string;
  repo_path: string;
  preset: string;
  onboarding_status: PanelOnboardingStatus;
  latest_run: PanelLatestRun;
  modules: PanelModule[];
};

export type PanelProjectDetailResponse = {
  generated_at: string;
  project: PanelProjectDetail;
};

function getApiBaseUrl(): string {
  return process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

export async function getPanelProjects(): Promise<PanelProjectsResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/panel/projects`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load panel projects: ${response.status}`);
  }

  return (await response.json()) as PanelProjectsResponse;
}

export async function getPanelProject(projectKey: string): Promise<PanelProjectDetailResponse | null> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/panel/projects/${projectKey}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to load panel project '${projectKey}': ${response.status}`);
  }

  return (await response.json()) as PanelProjectDetailResponse;
}
