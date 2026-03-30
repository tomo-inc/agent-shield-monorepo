from __future__ import annotations

from collections import defaultdict
from typing import cast

from app.db.models import PanelBaseline, PanelCheckerResult, PanelModule, PanelRun, PanelRunModule
from app.schemas.panel import (
    PanelCheckerName,
    PanelCheckerResult as PanelCheckerResultDto,
    PanelCheckerStatus,
    PanelHealthStatus,
    PanelLatestRun,
    PanelLatestRunRef,
    PanelOverviewProject,
    PanelProjectDetail,
    PanelRunModule as PanelRunModuleDto,
    PanelRunStatus,
)


def derive_health(status: PanelRunStatus) -> PanelHealthStatus:
    mapping: dict[PanelRunStatus, PanelHealthStatus] = {
        "pass": "healthy",
        "fail": "failing",
        "timeout": "warning",
        "blocked": "warning",
        "not-run": "unknown",
    }
    return mapping[status]


def as_checker_name(value: str) -> PanelCheckerName:
    return cast(PanelCheckerName, value)


def as_checker_status(value: str) -> PanelCheckerStatus:
    return cast(PanelCheckerStatus, value)


def as_run_status(value: str) -> PanelRunStatus:
    return cast(PanelRunStatus, value)


def assemble_run_modules(
    modules: list[PanelModule],
    run_modules: list[PanelRunModule],
    checker_results: list[PanelCheckerResult],
    baselines: list[PanelBaseline],
) -> list[PanelRunModuleDto]:
    module_by_id = {module.id: module for module in modules}
    baseline_by_module_id = {baseline.module_id: baseline.baseline_pct for baseline in baselines}
    checker_map: dict[int, list[PanelCheckerResultDto]] = defaultdict(list)
    for checker_result in checker_results:
        checker_map[checker_result.run_module_id].append(
            PanelCheckerResultDto(
                checker=as_checker_name(checker_result.checker),
                status=as_checker_status(checker_result.status),
                detail=checker_result.detail,
                duration_sec=checker_result.duration_sec,
            )
        )

    payloads: list[PanelRunModuleDto] = []
    for run_module in run_modules:
        module = module_by_id[run_module.module_id]
        payloads.append(
            PanelRunModuleDto(
                module_name=module.module_name,
                stack=run_module.stack or module.stack,
                language=run_module.language or module.language,
                status=as_run_status(run_module.status),
                coverage_pct=run_module.coverage_pct,
                baseline_pct=baseline_by_module_id.get(run_module.module_id, run_module.baseline_pct),
                coverage_gate_pct=run_module.coverage_gate_pct,
                coverage_delta_pct=run_module.coverage_delta_pct,
                coverage_parser=run_module.coverage_parser,
                block_reason=run_module.block_reason,
                checker_results=checker_map[run_module.id],
            )
        )
    return payloads


def build_latest_run_ref(run: PanelRun) -> PanelLatestRunRef:
    return PanelLatestRunRef(
        run_key=run.run_key,
        status=as_run_status(run.status),
        block_reason=run.block_reason,
        finished_at=run.finished_at or run.created_at,
    )


def build_latest_run_payload(run: PanelRun, modules: list[PanelRunModuleDto]) -> PanelLatestRun:
    return PanelLatestRun(
        run_key=run.run_key,
        source=run.source,
        git_ref=run.git_ref,
        git_sha=run.git_sha,
        triggered_by=run.triggered_by,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_sec=run.duration_sec,
        strict_mode=run.strict_mode,
        status=as_run_status(run.status),
        block_reason=run.block_reason,
        modules=modules,
    )


def build_overview_project(project, module_count: int, latest_run: PanelRun | None) -> PanelOverviewProject:
    status: PanelRunStatus = as_run_status(latest_run.status) if latest_run is not None else "not-run"
    return PanelOverviewProject(
        project_key=project.project_key,
        project_name=project.project_name,
        preset=project.preset,
        module_count=module_count,
        onboarding_status=project.onboarding_status,
        health=derive_health(status),
        check_all=status,
        last_run_at=latest_run.finished_at if latest_run is not None else None,
        block_reason=latest_run.block_reason if latest_run is not None else None,
    )


def build_project_detail(project, latest_run: PanelRun | None, modules: list[PanelRunModuleDto]) -> PanelProjectDetail:
    return PanelProjectDetail(
        project_key=project.project_key,
        project_name=project.project_name,
        preset=project.preset,
        onboarding_status=project.onboarding_status,
        latest_run=build_latest_run_ref(latest_run) if latest_run is not None else None,
        modules=modules,
    )
