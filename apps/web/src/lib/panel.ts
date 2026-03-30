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

type ApiOverviewProject = {
  project_key: string;
  project_name: string;
  preset: string;
  module_count: number;
  onboarding_status: PanelOnboardingStatus;
  health: PanelHealth;
  check_all: Exclude<PanelRunStatus, null>;
  last_run_at: string | null;
  block_reason: string | null;
};

type ApiProjectsResponse = {
  generated_at: string;
  projects: ApiOverviewProject[];
};

type ApiCheckerResult = PanelCheckerResult;

type ApiRunModule = {
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
  checker_results: ApiCheckerResult[];
};

type ApiLatestRunRef = {
  run_key: string;
  status: Exclude<PanelRunStatus, null>;
  block_reason: string | null;
  finished_at: string;
};

type ApiProjectDetail = {
  project_key: string;
  project_name: string;
  preset: string;
  onboarding_status: PanelOnboardingStatus;
  latest_run: ApiLatestRunRef | null;
  modules: ApiRunModule[];
};

type ApiProjectDetailResponse = {
  generated_at: string;
  project: ApiProjectDetail;
};

type ApiLatestRun = {
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
  modules: ApiRunModule[];
};

type ApiLatestRunResponse = {
  generated_at: string;
  run: ApiLatestRun;
};

function getApiBaseUrl(): string {
  return "http://127.0.0.1:8000";
}

function getFallbackRun(projectKey: string, project: ApiProjectDetail): PanelLatestRun {
  return {
    run_key: project.latest_run?.run_key ?? `${projectKey}-latest`,
    source: null,
    git_ref: null,
    git_sha: null,
    triggered_by: null,
    started_at: null,
    finished_at: project.latest_run?.finished_at ?? null,
    duration_sec: null,
    strict_mode: false,
    status: project.latest_run?.status ?? "not-run",
    block_reason: project.latest_run?.block_reason ?? null,
  };
}

function mapOverviewProject(project: ApiOverviewProject): PanelProject {
  return {
    project_key: project.project_key,
    project_name: project.project_name,
    repo_path: project.project_key,
    preset: project.preset,
    onboarding_status: project.onboarding_status,
    module_count: project.module_count,
    health: project.health,
    source: null,
    triggered_by: null,
    status: project.check_all,
    block_reason: project.block_reason,
    started_at: null,
    finished_at: project.last_run_at,
    duration_sec: null,
  };
}

function mapProjectDetail(project: ApiProjectDetail, latestRun: ApiLatestRun | null): PanelProjectDetail {
  return {
    project_key: project.project_key,
    project_name: project.project_name,
    repo_path: project.project_key,
    preset: project.preset,
    onboarding_status: project.onboarding_status,
    latest_run: latestRun
      ? {
          run_key: latestRun.run_key,
          source: latestRun.source,
          git_ref: latestRun.git_ref,
          git_sha: latestRun.git_sha,
          triggered_by: latestRun.triggered_by,
          started_at: latestRun.started_at,
          finished_at: latestRun.finished_at,
          duration_sec: latestRun.duration_sec,
          strict_mode: latestRun.strict_mode,
          status: latestRun.status,
          block_reason: latestRun.block_reason,
        }
      : getFallbackRun(project.project_key, project),
    modules: latestRun?.modules ?? project.modules,
  };
}

export async function getPanelProjects(): Promise<PanelProjectsResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/panel/projects`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load panel projects: ${response.status}`);
  }

  const data = (await response.json()) as ApiProjectsResponse;

  return {
    generated_at: data.generated_at,
    projects: data.projects.map(mapOverviewProject),
  };
}

export async function getPanelProject(projectKey: string): Promise<PanelProjectDetailResponse | null> {
  const detailResponse = await fetch(`${getApiBaseUrl()}/api/v1/panel/projects/${projectKey}`, {
    cache: "no-store",
  });

  if (detailResponse.status === 404) {
    return null;
  }

  if (!detailResponse.ok) {
    throw new Error(`Failed to load panel project '${projectKey}': ${detailResponse.status}`);
  }

  const detailData = (await detailResponse.json()) as ApiProjectDetailResponse;

  const latestResponse = await fetch(`${getApiBaseUrl()}/api/v1/panel/projects/${projectKey}/latest`, {
    cache: "no-store",
  });

  let latestRun: ApiLatestRun | null = null;

  if (latestResponse.ok) {
    const latestData = (await latestResponse.json()) as ApiLatestRunResponse;
    latestRun = latestData.run;
  } else if (latestResponse.status !== 404) {
    throw new Error(`Failed to load latest panel run for '${projectKey}': ${latestResponse.status}`);
  }

  return {
    generated_at: detailData.generated_at,
    project: mapProjectDetail(detailData.project, latestRun),
  };
}
