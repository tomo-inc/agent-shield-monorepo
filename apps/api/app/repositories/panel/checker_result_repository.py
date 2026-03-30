from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PanelCheckerResult
from app.repositories.panel.common import build_upsert, utc_now


class CheckerResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        run_id: int,
        run_module_id: int,
        checker: str,
        status: str,
        detail: str | None,
        duration_sec: float | None,
    ) -> PanelCheckerResult:
        values = {
            "run_id": run_id,
            "run_module_id": run_module_id,
            "checker": checker,
            "status": status,
            "detail": detail,
            "duration_sec": duration_sec,
            "created_at": utc_now(),
        }
        statement = build_upsert(
            self.session,
            PanelCheckerResult.__table__,
            values,
            index_elements=["run_module_id", "checker"],
            update_columns=["run_id", "status", "detail", "duration_sec"],
        )
        self.session.execute(statement)
        return self.session.execute(
            select(PanelCheckerResult).where(
                PanelCheckerResult.run_module_id == run_module_id,
                PanelCheckerResult.checker == checker,
            )
        ).scalar_one()

    def list_for_run(self, run_id: int) -> list[PanelCheckerResult]:
        return list(
            self.session.execute(
                select(PanelCheckerResult)
                .where(PanelCheckerResult.run_id == run_id)
                .order_by(PanelCheckerResult.run_module_id.asc(), PanelCheckerResult.checker.asc())
            ).scalars()
        )
