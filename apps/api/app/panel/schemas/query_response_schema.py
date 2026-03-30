from typing import Literal

from pydantic import BaseModel, Field


class PanelProjectItem(BaseModel):
    project_key: str = Field(description="Project unique key")
    project_name: str = Field(description="Project display name")
    repo_path: str = Field(description="Repository path")
    preset: str = Field(description="CLI detected preset")
    onboarding_status: Literal["ready", "pending", "blocked", "custom-needed"] = (
        Field(description="Project onboarding status")
    )
    module_count: int = Field(description="Derived module count for the project")
    health: Literal["healthy", "warning", "failing", "unknown"] = Field(
        description="Derived project health from the latest run status"
    )
    source: str | None = Field(description="Latest run source")
    triggered_by: str | None = Field(description="Latest run trigger actor")
    status: Literal["pass", "fail", "timeout", "blocked", "not-run"] | None = Field(
        description="Latest project run status"
    )
    block_reason: str | None = Field(description="Latest project block reason")
    started_at: str | None = Field(description="Latest run start time in ISO 8601 UTC")
    finished_at: str | None = Field(description="Latest run finish time in ISO 8601 UTC")
    duration_sec: float | None = Field(description="Latest run duration in seconds")


class PanelProjectsResponse(BaseModel):
    generated_at: str = Field(description="Response generation time in ISO 8601 UTC")
    projects: list[PanelProjectItem] = Field(description="Supported panel projects")


class PanelCheckerResultItem(BaseModel):
    checker: Literal["build", "lint", "typecheck", "test", "coverage"] = Field(
        description="Checker name"
    )
    status: Literal["pass", "fail", "timeout", "skip"] = Field(
        description="Checker execution status"
    )
    detail: str | None = Field(description="Checker output summary")
    duration_sec: float | None = Field(description="Checker duration in seconds")


class PanelModuleDetailItem(BaseModel):
    module_name: str = Field(description="Module name")
    stack: str | None = Field(description="Module stack description")
    language: str | None = Field(description="Primary module language")
    status: Literal["pass", "fail", "timeout", "blocked", "not-run"] = Field(
        description="Current module status"
    )
    coverage_pct: float | None = Field(description="Current module coverage percentage")
    baseline_pct: float | None = Field(description="Current module baseline coverage percentage")
    coverage_gate_pct: float | None = Field(description="Current module coverage gate percentage")
    coverage_delta_pct: float | None = Field(
        description="Current module coverage delta percentage"
    )
    coverage_parser: str | None = Field(description="Coverage parser identifier")
    block_reason: str | None = Field(description="Current module block reason")
    checker_results: list[PanelCheckerResultItem] = Field(
        description="Checker results for the latest run"
    )


class PanelLatestRunDetail(BaseModel):
    run_key: str = Field(description="Run unique key")
    source: str | None = Field(description="Latest run source")
    git_ref: str | None = Field(description="Git ref for the latest run")
    git_sha: str | None = Field(description="Git SHA for the latest run")
    triggered_by: str | None = Field(description="Latest run trigger actor")
    started_at: str | None = Field(description="Latest run start time in ISO 8601 UTC")
    finished_at: str | None = Field(description="Latest run finish time in ISO 8601 UTC")
    duration_sec: float | None = Field(description="Latest run duration in seconds")
    strict_mode: bool = Field(description="Whether the latest run used strict mode")
    status: Literal["pass", "fail", "timeout", "blocked", "not-run"] = Field(
        description="Latest project run status"
    )
    block_reason: str | None = Field(description="Latest project block reason")


class PanelProjectDetailPayload(BaseModel):
    project_key: str = Field(description="Project unique key")
    project_name: str = Field(description="Project display name")
    repo_path: str = Field(description="Repository path")
    preset: str = Field(description="CLI detected preset")
    onboarding_status: Literal["ready", "pending", "blocked", "custom-needed"] = (
        Field(description="Project onboarding status")
    )
    latest_run: PanelLatestRunDetail = Field(description="Latest project run detail")
    modules: list[PanelModuleDetailItem] = Field(description="Project module details")


class PanelProjectDetailResponse(BaseModel):
    generated_at: str = Field(description="Response generation time in ISO 8601 UTC")
    project: PanelProjectDetailPayload = Field(description="Panel project detail record")


class PanelProjectLatestRunResponse(BaseModel):
    generated_at: str = Field(description="Response generation time in ISO 8601 UTC")
    project_key: str = Field(description="Project unique key")
    source: str | None = Field(description="Latest run source")
    triggered_by: str | None = Field(description="Latest run trigger actor")
    status: Literal["pass", "fail", "timeout", "blocked", "not-run"] | None = Field(
        description="Latest project run status"
    )
    block_reason: str | None = Field(description="Latest project block reason")
    started_at: str | None = Field(description="Latest run start time in ISO 8601 UTC")
    finished_at: str | None = Field(description="Latest run finish time in ISO 8601 UTC")
    duration_sec: float | None = Field(description="Latest run duration in seconds")
