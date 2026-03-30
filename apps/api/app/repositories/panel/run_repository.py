from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PanelRun
from app.repositories.panel.common import build_upsert, utc_now


class RunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        project_id: int,
        run_key: str,
        source: str | None,
        git_ref: str | None,
        git_sha: str | None,
        triggered_by: str | None,
        started_at,
        finished_at,
        duration_sec: float | None,
        strict_mode: bool,
        status: str,
        block_reason: str | None,
    ) -> PanelRun:
        values = {
            "project_id": project_id,
            "run_key": run_key,
            "source": source,
            "git_ref": git_ref,
            "git_sha": git_sha,
            "triggered_by": triggered_by,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_sec": duration_sec,
            "strict_mode": strict_mode,
            "status": status,
            "block_reason": block_reason,
            "created_at": utc_now(),
        }
        statement = build_upsert(
            self.session,
            PanelRun.__table__,
            values,
            index_elements=["run_key"],
            update_columns=[
                "project_id",
                "source",
                "git_ref",
                "git_sha",
                "triggered_by",
                "started_at",
                "finished_at",
                "duration_sec",
                "strict_mode",
                "status",
                "block_reason",
            ],
        )
        self.session.execute(statement)
        return self.session.execute(select(PanelRun).where(PanelRun.run_key == run_key)).scalar_one()

    def get_latest_for_project(self, project_id: int) -> PanelRun | None:
        return self.session.execute(
            select(PanelRun)
            .where(PanelRun.project_id == project_id)
            .order_by(PanelRun.finished_at.desc().nulls_last(), PanelRun.id.desc())
        ).scalars().first()
