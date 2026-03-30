from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PanelBaseline
from app.repositories.panel.common import build_upsert


class BaselineRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, *, project_id: int, module_id: int, baseline_pct: float, updated_at) -> PanelBaseline:
        values = {
            "project_id": project_id,
            "module_id": module_id,
            "baseline_pct": baseline_pct,
            "updated_at": updated_at,
        }
        statement = build_upsert(
            self.session,
            PanelBaseline.__table__,
            values,
            index_elements=["project_id", "module_id"],
            update_columns=["baseline_pct", "updated_at"],
        )
        self.session.execute(statement)
        return self.session.execute(
            select(PanelBaseline).where(
                PanelBaseline.project_id == project_id, PanelBaseline.module_id == module_id
            )
        ).scalar_one()

    def list_for_project(self, project_id: int) -> list[PanelBaseline]:
        return list(
            self.session.execute(
                select(PanelBaseline).where(PanelBaseline.project_id == project_id)
            ).scalars()
        )
