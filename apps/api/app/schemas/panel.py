from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PanelCheckerName = Literal["build", "lint", "typecheck", "test", "coverage"]
PanelCheckerStatus = Literal["pass", "fail", "timeout", "skip"]
PanelRunStatus = Literal["pass", "fail", "timeout", "blocked", "not-run"]
PanelOnboardingStatus = Literal["ready", "pending", "blocked", "custom-needed"]
PanelHealthStatus = Literal["healthy", "warning", "failing", "unknown"]


class PanelProjectModule(BaseModel):
    module_name: str = Field(description="Module path, such as apps/api")
    stack: str | None = Field(default=None, description="Detected stack summary")
    language: str | None = Field(default=None, description="Primary language label")


class PanelProjectCommands(BaseModel):
    build: str | None = Field(default=None, description="Build command")
    lint: str | None = Field(default=None, description="Lint command")
    typecheck: str | None = Field(default=None, description="Typecheck command")
    test: str | None = Field(default=None, description="Test command")
    coverage: str | None = Field(default=None, description="Coverage command")


class PanelProjectThresholds(BaseModel):
    coverage_tolerance_pct: float | None = Field(default=None, description="Coverage tolerance percentage")
    coverage_floor_pct: float | None = Field(default=None, description="Coverage floor percentage")
    lint_max_errors: int | None = Field(default=None, description="Maximum lint errors")
    typecheck_max_errors: int | None = Field(default=None, description="Maximum typecheck errors")


class PanelProjectTimeouts(BaseModel):
    build: int | None = Field(default=None, description="Build timeout in seconds")
    test: int | None = Field(default=None, description="Test timeout in seconds")


class PanelProjectNotify(BaseModel):
    feishu_webhook: str | None = Field(default=None, description="Feishu webhook URL")


class PanelProjectRegisterRequest(BaseModel):
    project_key: str = Field(description="Stable project identifier")
    project_name: str = Field(description="Display name")
    repo_path: str = Field(description="Repository path")
    preset: str = Field(description="CLI resolved preset")
    onboarding_status: PanelOnboardingStatus = Field(description="Current onboarding state")
    commands: PanelProjectCommands | None = Field(default=None, description="Project-level commands")
    thresholds: PanelProjectThresholds | None = Field(default=None, description="Threshold configuration")
    timeouts: PanelProjectTimeouts | None = Field(default=None, description="Timeout configuration")
    notify: PanelProjectNotify | None = Field(default=None, description="Notification configuration")
    modules: list[PanelProjectModule] = Field(description="Detected module list")


class PanelProjectRegisterResponse(BaseModel):
    ok: bool = Field(description="Whether the request succeeded")
    project_id: int = Field(description="Resolved project id")
    module_count: int = Field(description="Number of modules upserted")


class PanelBaselineModule(BaseModel):
    module_name: str = Field(description="Module path, such as apps/api")
    baseline_pct: float = Field(description="Effective baseline coverage percentage")


class PanelBaselineUploadRequest(BaseModel):
    project_key: str = Field(description="Stable project identifier")
    updated_at: datetime = Field(description="Baseline update timestamp")
    modules: list[PanelBaselineModule] = Field(description="Baseline rows to upload")


class PanelBaselineUploadResponse(BaseModel):
    ok: bool = Field(description="Whether the request succeeded")
    project_id: int = Field(description="Resolved project id")
    baselines_upserted: int = Field(description="Number of baseline rows upserted")


class PanelCheckerResult(BaseModel):
    checker: PanelCheckerName = Field(description="Checker name")
    status: PanelCheckerStatus = Field(description="Checker execution status")
    detail: str | None = Field(default=None, description="Checker output summary")
    duration_sec: float | None = Field(default=None, description="Checker duration in seconds")


class PanelRunModule(BaseModel):
    module_name: str = Field(description="Module path, such as apps/api")
    stack: str | None = Field(default=None, description="Runtime stack summary")
    language: str | None = Field(default=None, description="Runtime language label")
    status: PanelRunStatus = Field(description="Module status for this run")
    coverage_pct: float | None = Field(default=None, description="Current line coverage")
    baseline_pct: float | None = Field(default=None, description="Baseline echoed in this run")
    coverage_gate_pct: float | None = Field(default=None, description="Coverage gate threshold")
    coverage_delta_pct: float | None = Field(default=None, description="Coverage delta versus baseline")
    coverage_parser: str | None = Field(default=None, description="Coverage parser type")
    block_reason: str | None = Field(default=None, description="Module blocking reason")
    checker_results: list[PanelCheckerResult] = Field(description="Checker result list")


class PanelRunUploadRequest(BaseModel):
    project_key: str = Field(description="Stable project identifier")
    run_key: str = Field(description="Idempotent run identifier")
    source: str | None = Field(default=None, description="Run source")
    git_ref: str | None = Field(default=None, description="Branch or tag")
    git_sha: str | None = Field(default=None, description="Commit SHA")
    triggered_by: str | None = Field(default=None, description="Trigger user or system")
    started_at: datetime | None = Field(default=None, description="Run start timestamp")
    finished_at: datetime | None = Field(default=None, description="Run finish timestamp")
    duration_sec: float | None = Field(default=None, description="Total duration")
    strict_mode: bool = Field(description="Whether strict mode was enabled")
    status: PanelRunStatus = Field(description="Project-level run status")
    block_reason: str | None = Field(default=None, description="Project-level blocking reason")
    modules: list[PanelRunModule] = Field(description="Per-module run snapshots")


class PanelRunUploadResponse(BaseModel):
    ok: bool = Field(description="Whether the request succeeded")
    project_id: int = Field(description="Resolved project id")
    run_id: int = Field(description="Resolved run id")
    modules_upserted: int = Field(description="Number of run modules upserted")
    checker_results_upserted: int = Field(description="Number of checker rows upserted")


class PanelLatestRunRef(BaseModel):
    run_key: str = Field(description="Run identifier")
    status: PanelRunStatus = Field(description="Project-level run status")
    block_reason: str | None = Field(default=None, description="Project-level blocking reason")
    finished_at: datetime = Field(description="Run finish timestamp")


class PanelOverviewProject(BaseModel):
    project_key: str = Field(description="Stable project identifier")
    project_name: str = Field(description="Display name")
    preset: str = Field(description="CLI resolved preset")
    module_count: int = Field(description="Number of modules under the project")
    onboarding_status: PanelOnboardingStatus = Field(description="Current onboarding state")
    health: PanelHealthStatus = Field(description="Derived project health")
    check_all: PanelRunStatus = Field(description="Derived latest project status")
    last_run_at: datetime | None = Field(default=None, description="Latest synchronized run time")
    block_reason: str | None = Field(default=None, description="Latest synchronized block reason")


class PanelProjectOverviewResponse(BaseModel):
    generated_at: datetime = Field(description="Response generation time")
    projects: list[PanelOverviewProject] = Field(description="Overview rows")


class PanelProjectDetail(BaseModel):
    project_key: str = Field(description="Stable project identifier")
    project_name: str = Field(description="Display name")
    preset: str = Field(description="CLI resolved preset")
    onboarding_status: PanelOnboardingStatus = Field(description="Current onboarding state")
    latest_run: PanelLatestRunRef | None = Field(default=None, description="Latest run summary")
    modules: list[PanelRunModule] = Field(description="Latest run module cards")


class PanelProjectDetailResponse(BaseModel):
    generated_at: datetime = Field(description="Response generation time")
    project: PanelProjectDetail = Field(description="Project detail payload")


class PanelLatestRun(BaseModel):
    run_key: str = Field(description="Run identifier")
    source: str | None = Field(default=None, description="Run source")
    git_ref: str | None = Field(default=None, description="Branch or tag")
    git_sha: str | None = Field(default=None, description="Commit SHA")
    triggered_by: str | None = Field(default=None, description="Trigger user or system")
    started_at: datetime | None = Field(default=None, description="Run start timestamp")
    finished_at: datetime | None = Field(default=None, description="Run finish timestamp")
    duration_sec: float | None = Field(default=None, description="Total duration")
    strict_mode: bool = Field(description="Whether strict mode was enabled")
    status: PanelRunStatus = Field(description="Project-level run status")
    block_reason: str | None = Field(default=None, description="Project-level blocking reason")
    modules: list[PanelRunModule] = Field(description="Per-module run snapshots")


class PanelLatestRunResponse(BaseModel):
    generated_at: datetime = Field(description="Response generation time")
    run: PanelLatestRun = Field(description="Latest run payload")
