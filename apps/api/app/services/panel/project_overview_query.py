from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.repositories.panel.run_repository import RunRepository
from app.schemas.panel import PanelProjectOverviewResponse
from app.services.panel.common import build_overview_project


def get_project_overview(session: Session) -> PanelProjectOverviewResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)
    run_repository = RunRepository(session)

    projects = []
    for project in project_repository.list_all():
        module_count = module_repository.count_for_project(project.id)
        latest_run = run_repository.get_latest_for_project(project.id)
        projects.append(build_overview_project(project, module_count, latest_run))
    return PanelProjectOverviewResponse(generated_at=datetime.now(UTC), projects=projects)
