from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PanelModule
from app.repositories.panel.common import build_upsert, utc_now


class ModuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def resolve_or_create(
        self, *, project_id: int, module_name: str, stack: str | None, language: str | None
    ) -> PanelModule:
        now = utc_now()
        values = {
            "project_id": project_id,
            "module_name": module_name,
            "stack": stack,
            "language": language,
            "created_at": now,
            "updated_at": now,
        }
        statement = build_upsert(
            self.session,
            PanelModule.__table__,
            values,
            index_elements=["project_id", "module_name"],
            update_columns=["stack", "language", "updated_at"],
        )
        self.session.execute(statement)
        return self.session.execute(
            select(PanelModule).where(
                PanelModule.project_id == project_id, PanelModule.module_name == module_name
            )
        ).scalar_one()

    def list_for_project(self, project_id: int) -> list[PanelModule]:
        return list(
            self.session.execute(
                select(PanelModule)
                .where(PanelModule.project_id == project_id)
                .order_by(PanelModule.module_name.asc())
            ).scalars()
        )

    def count_for_project(self, project_id: int) -> int:
        return int(
            self.session.execute(
                select(func.count()).select_from(PanelModule).where(PanelModule.project_id == project_id)
            ).scalar_one()
        )
