from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.panel.baseline_repository import BaselineRepository
from app.repositories.panel.checker_result_repository import CheckerResultRepository
from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.repositories.panel.run_module_repository import RunModuleRepository
from app.repositories.panel.run_repository import RunRepository
from app.schemas.panel import PanelProjectDetailResponse
from app.services.panel.common import assemble_run_modules, build_project_detail
from app.services.panel.errors import ProjectNotFoundError


def get_project_detail(session: Session, project_key: str) -> PanelProjectDetailResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)
    baseline_repository = BaselineRepository(session)
    run_repository = RunRepository(session)
    run_module_repository = RunModuleRepository(session)
    checker_result_repository = CheckerResultRepository(session)

    project = project_repository.get_by_key(project_key)
    if project is None:
        raise ProjectNotFoundError(project_key)

    modules = module_repository.list_for_project(project.id)
    baselines = baseline_repository.list_for_project(project.id)
    latest_run = run_repository.get_latest_for_project(project.id)
    assembled_modules = []
    if latest_run is not None:
        run_modules = run_module_repository.list_for_run(latest_run.id)
        checker_results = checker_result_repository.list_for_run(latest_run.id)
        assembled_modules = assemble_run_modules(modules, run_modules, checker_results, baselines)

    detail = build_project_detail(project, latest_run, assembled_modules)
    return PanelProjectDetailResponse(generated_at=datetime.now(UTC), project=detail)
