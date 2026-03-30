from sqlalchemy.orm import Session

from app.repositories.panel.module_repository import ModuleRepository
from app.repositories.panel.project_repository import ProjectRepository
from app.schemas.panel import PanelProjectRegisterRequest, PanelProjectRegisterResponse


def register_project(session: Session, payload: PanelProjectRegisterRequest) -> PanelProjectRegisterResponse:
    project_repository = ProjectRepository(session)
    module_repository = ModuleRepository(session)

    project = project_repository.upsert(
        project_key=payload.project_key,
        project_name=payload.project_name,
        repo_path=payload.repo_path,
        preset=payload.preset,
        onboarding_status=payload.onboarding_status,
        commands_json=payload.commands.model_dump(exclude_none=True) if payload.commands else None,
        thresholds_json=payload.thresholds.model_dump(exclude_none=True) if payload.thresholds else None,
        timeouts_json=payload.timeouts.model_dump(exclude_none=True) if payload.timeouts else None,
        notify_json=payload.notify.model_dump(exclude_none=True) if payload.notify else None,
    )
    for module in payload.modules:
        module_repository.resolve_or_create(
            project_id=project.id,
            module_name=module.module_name,
            stack=module.stack,
            language=module.language,
        )
    session.commit()
    return PanelProjectRegisterResponse(ok=True, project_id=project.id, module_count=len(payload.modules))
