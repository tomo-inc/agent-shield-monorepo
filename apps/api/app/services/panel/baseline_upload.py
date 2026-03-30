from sqlalchemy.orm import Session

from app.repositories.panel.baseline_repository import BaselineRepository
from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.schemas.panel import PanelBaselineUploadRequest, PanelBaselineUploadResponse
from app.services.panel.errors import ProjectNotFoundError


def upload_baselines(session: Session, payload: PanelBaselineUploadRequest) -> PanelBaselineUploadResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)
    baseline_repository = BaselineRepository(session)

    project = project_repository.get_by_key(payload.project_key)
    if project is None:
        raise ProjectNotFoundError(payload.project_key)

    for module in payload.modules:
        module_record = module_repository.resolve_or_create(
            project_id=project.id,
            module_name=module.module_name,
            stack=None,
            language=None,
        )
        baseline_repository.upsert(
            project_id=project.id,
            module_id=module_record.id,
            baseline_pct=module.baseline_pct,
            updated_at=payload.updated_at,
        )
    session.commit()
    return PanelBaselineUploadResponse(
        ok=True, project_id=project.id, baselines_upserted=len(payload.modules)
    )
