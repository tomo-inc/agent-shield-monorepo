from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.repositories.panel.run_module_repository import RunModuleRepository
from app.repositories.panel.run_repository import RunRepository
from app.schemas.panel import PanelProjectOverviewResponse
from app.services.panel.common import build_overview_project, calculate_coverage_average


def get_project_overview(session: Session) -> PanelProjectOverviewResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)
    run_repository = RunRepository(session)
    run_module_repository = RunModuleRepository(session)

    projects = []
    for project in project_repository.list_all():
        module_count = module_repository.count_for_project(project.id)
        latest_run = run_repository.get_latest_for_project(project.id)
        coverage_values = run_module_repository.coverage_values_for_run(latest_run.id) if latest_run is not None else []
        coverage_avg_pct = calculate_coverage_average(coverage_values)
        projects.append(build_overview_project(project, module_count, latest_run, coverage_avg_pct))
    return PanelProjectOverviewResponse(generated_at=datetime.now(UTC), projects=projects)
