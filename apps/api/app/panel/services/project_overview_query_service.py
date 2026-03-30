from datetime import UTC, datetime
from typing import Final, Literal

from app.panel.schemas.query_response_schema import (
    PanelCheckerResultItem,
    PanelLatestRunDetail,
    PanelModuleDetailItem,
    PanelProjectDetailPayload,
    PanelProjectDetailResponse,
    PanelProjectItem,
    PanelProjectLatestRunResponse,
    PanelProjectsResponse,
)

_PANEL_PROJECT_DETAILS_BY_KEY: Final[dict[str, PanelProjectDetailPayload]] = {
    "agent-shield-monorepo": PanelProjectDetailPayload(
        project_key="agent-shield-monorepo",
        project_name="AgentShield Monorepo",
        repo_path="/workspace/agent-shield-monorepo",
        preset="infer-monorepo",
        onboarding_status="ready",
        latest_run=PanelLatestRunDetail(
            run_key="agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
            source="local-cli",
            git_ref="main",
            git_sha="abc123",
            triggered_by="dawei",
            started_at="2026-03-30T10:00:00Z",
            finished_at="2026-03-30T10:00:31Z",
            duration_sec=31.0,
            strict_mode=True,
            status="fail",
            block_reason="apps/web coverage below gate",
        ),
        modules=[
            PanelModuleDetailItem(
                module_name="apps/api",
                stack="Python / FastAPI",
                language="Python",
                status="pass",
                coverage_pct=81.2,
                baseline_pct=81.0,
                coverage_gate_pct=76.0,
                coverage_delta_pct=0.2,
                coverage_parser="pytest-cov-json",
                block_reason=None,
                checker_results=[
                    PanelCheckerResultItem(
                        checker="build", status="pass", detail="", duration_sec=3.2
                    ),
                    PanelCheckerResultItem(
                        checker="lint", status="pass", detail="", duration_sec=2.1
                    ),
                    PanelCheckerResultItem(
                        checker="typecheck", status="pass", detail="", duration_sec=4.5
                    ),
                    PanelCheckerResultItem(
                        checker="test",
                        status="pass",
                        detail="86 passed / 0 failed",
                        duration_sec=10.0,
                    ),
                    PanelCheckerResultItem(
                        checker="coverage",
                        status="pass",
                        detail="Line 81.2%, gate >= 76.0%",
                        duration_sec=1.0,
                    ),
                ],
            ),
            PanelModuleDetailItem(
                module_name="apps/web",
                stack="TypeScript / Next.js",
                language="TypeScript",
                status="fail",
                coverage_pct=58.3,
                baseline_pct=72.0,
                coverage_gate_pct=67.0,
                coverage_delta_pct=-13.7,
                coverage_parser="istanbul-json",
                block_reason="coverage below gate",
                checker_results=[
                    PanelCheckerResultItem(
                        checker="build", status="pass", detail="", duration_sec=12.3
                    ),
                    PanelCheckerResultItem(
                        checker="lint", status="pass", detail="", duration_sec=3.4
                    ),
                    PanelCheckerResultItem(
                        checker="typecheck", status="pass", detail="", duration_sec=5.2
                    ),
                    PanelCheckerResultItem(
                        checker="test",
                        status="pass",
                        detail="43 passed / 0 failed",
                        duration_sec=8.0,
                    ),
                    PanelCheckerResultItem(
                        checker="coverage",
                        status="fail",
                        detail="Line 58.3%, gate >= 67.0%",
                        duration_sec=1.3,
                    ),
                ],
            ),
        ],
    ),
    "agentpay-sdk-internal": PanelProjectDetailPayload(
        project_key="agentpay-sdk-internal",
        project_name="AgentPay SDK Internal",
        repo_path="/workspace/agentpay-sdk-internal",
        preset="agentpay-sdk",
        onboarding_status="pending",
        latest_run=PanelLatestRunDetail(
            run_key="agentpay-sdk-internal_def456_2026-03-29T08:00:00Z_github-actions",
            source="github-actions",
            git_ref="main",
            git_sha="def456",
            triggered_by="ci-bot",
            started_at="2026-03-29T08:00:00Z",
            finished_at="2026-03-29T08:00:24Z",
            duration_sec=24.0,
            strict_mode=True,
            status="pass",
            block_reason=None,
        ),
        modules=[
            PanelModuleDetailItem(
                module_name="sdk/python",
                stack="Python / SDK",
                language="Python",
                status="pass",
                coverage_pct=84.0,
                baseline_pct=82.0,
                coverage_gate_pct=77.0,
                coverage_delta_pct=2.0,
                coverage_parser="pytest-cov-json",
                block_reason=None,
                checker_results=[
                    PanelCheckerResultItem(
                        checker="build", status="pass", detail="", duration_sec=2.4
                    ),
                    PanelCheckerResultItem(
                        checker="lint", status="pass", detail="", duration_sec=1.9
                    ),
                    PanelCheckerResultItem(
                        checker="typecheck", status="pass", detail="", duration_sec=3.0
                    ),
                    PanelCheckerResultItem(
                        checker="test",
                        status="pass",
                        detail="57 passed / 0 failed",
                        duration_sec=7.2,
                    ),
                    PanelCheckerResultItem(
                        checker="coverage",
                        status="pass",
                        detail="Line 84.0%, gate >= 77.0%",
                        duration_sec=0.9,
                    ),
                ],
            )
        ],
    ),
}


def _generated_at() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _derive_health(
    status: Literal["pass", "fail", "timeout", "blocked", "not-run"]
) -> Literal["healthy", "warning", "failing", "unknown"]:
    if status == "pass":
        return "healthy"
    if status == "fail":
        return "failing"
    if status in {"timeout", "blocked"}:
        return "warning"
    return "unknown"


def get_project_overview() -> PanelProjectsResponse:
    projects = [
        PanelProjectItem(
            project_key=project.project_key,
            project_name=project.project_name,
            repo_path=project.repo_path,
            preset=project.preset,
            onboarding_status=project.onboarding_status,
            module_count=len(project.modules),
            health=_derive_health(project.latest_run.status),
            source=project.latest_run.source,
            triggered_by=project.latest_run.triggered_by,
            status=project.latest_run.status,
            block_reason=project.latest_run.block_reason,
            started_at=project.latest_run.started_at,
            finished_at=project.latest_run.finished_at,
            duration_sec=project.latest_run.duration_sec,
        )
        for project in _PANEL_PROJECT_DETAILS_BY_KEY.values()
    ]
    return PanelProjectsResponse(generated_at=_generated_at(), projects=projects)


def get_project_detail(project_key: str) -> PanelProjectDetailResponse | None:
    project = _PANEL_PROJECT_DETAILS_BY_KEY.get(project_key)
    if project is None:
        return None

    return PanelProjectDetailResponse(generated_at=_generated_at(), project=project)


def get_project_latest_run(project_key: str) -> PanelProjectLatestRunResponse | None:
    project = _PANEL_PROJECT_DETAILS_BY_KEY.get(project_key)
    if project is None:
        return None

    latest_run = project.latest_run
    return PanelProjectLatestRunResponse(
        generated_at=_generated_at(),
        project_key=project.project_key,
        source=latest_run.source,
        triggered_by=latest_run.triggered_by,
        status=latest_run.status,
        block_reason=latest_run.block_reason,
        started_at=latest_run.started_at,
        finished_at=latest_run.finished_at,
        duration_sec=latest_run.duration_sec,
    )
