from sqlalchemy.orm import Session

from app.repositories.panel.checker_result_repository import CheckerResultRepository
from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.repositories.panel.run_module_repository import RunModuleRepository
from app.repositories.panel.run_repository import RunRepository
from app.schemas.panel import PanelRunUploadRequest, PanelRunUploadResponse
from app.services.panel.errors import ProjectNotFoundError


def upload_run(session: Session, payload: PanelRunUploadRequest) -> PanelRunUploadResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)
    run_repository = RunRepository(session)
    run_module_repository = RunModuleRepository(session)
    checker_result_repository = CheckerResultRepository(session)

    project = project_repository.get_by_key(payload.project_key)
    if project is None:
        raise ProjectNotFoundError(payload.project_key)

    run = run_repository.upsert(
        project_id=project.id,
        run_key=payload.run_key,
        source=payload.source,
        git_ref=payload.git_ref,
        git_sha=payload.git_sha,
        triggered_by=payload.triggered_by,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        duration_sec=payload.duration_sec,
        strict_mode=payload.strict_mode,
        status=payload.status,
        block_reason=payload.block_reason,
    )
    checker_count = 0
    for module in payload.modules:
        module_record = module_repository.resolve_or_create(
            project_id=project.id,
            module_name=module.module_name,
            stack=module.stack,
            language=module.language,
        )
        run_module = run_module_repository.upsert(
            run_id=run.id,
            module_id=module_record.id,
            stack=module.stack,
            language=module.language,
            status=module.status,
            coverage_pct=module.coverage_pct,
            baseline_pct=module.baseline_pct,
            coverage_gate_pct=module.coverage_gate_pct,
            coverage_delta_pct=module.coverage_delta_pct,
            coverage_parser=module.coverage_parser,
            block_reason=module.block_reason,
        )
        for checker in module.checker_results:
            checker_result_repository.upsert(
                run_id=run.id,
                run_module_id=run_module.id,
                checker=checker.checker,
                status=checker.status,
                detail=checker.detail,
                duration_sec=checker.duration_sec,
            )
            checker_count += 1
    session.commit()
    return PanelRunUploadResponse(
        ok=True,
        project_id=project.id,
        run_id=run.id,
        modules_upserted=len(payload.modules),
        checker_results_upserted=checker_count,
    )
