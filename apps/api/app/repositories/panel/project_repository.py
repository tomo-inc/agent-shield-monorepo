from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PanelProject
from app.repositories.panel.common import build_upsert, utc_now


class ProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_key(self, project_key: str) -> PanelProject | None:
        return self.session.execute(
            select(PanelProject).where(PanelProject.project_key == project_key)
        ).scalar_one_or_none()

    def list_all(self) -> list[PanelProject]:
        return list(
            self.session.execute(select(PanelProject).order_by(PanelProject.project_key.asc())).scalars()
        )

    def upsert(
        self,
        *,
        project_key: str,
        project_name: str,
        repo_path: str,
        preset: str | None,
        onboarding_status: str,
        commands_json: dict[str, str] | None,
        thresholds_json: dict[str, object] | None,
        timeouts_json: dict[str, int] | None,
        notify_json: dict[str, str] | None,
    ) -> PanelProject:
        now = utc_now()
        values = {
            "project_key": project_key,
            "project_name": project_name,
            "repo_path": repo_path,
            "preset": preset,
            "onboarding_status": onboarding_status,
            "commands_json": commands_json,
            "thresholds_json": thresholds_json,
            "timeouts_json": timeouts_json,
            "notify_json": notify_json,
            "created_at": now,
            "updated_at": now,
        }
        statement = build_upsert(
            self.session,
            PanelProject.__table__,
            values,
            index_elements=["project_key"],
            update_columns=[
                "project_name",
                "repo_path",
                "preset",
                "onboarding_status",
                "commands_json",
                "thresholds_json",
                "timeouts_json",
                "notify_json",
                "updated_at",
            ],
        )
        self.session.execute(statement)
        return self.session.execute(
            select(PanelProject).where(PanelProject.project_key == project_key)
        ).scalar_one()
