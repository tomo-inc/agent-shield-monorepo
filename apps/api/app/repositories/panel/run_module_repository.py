from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PanelRunModule
from app.repositories.panel.common import build_upsert, utc_now


class RunModuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        run_id: int,
        module_id: int,
        stack: str | None,
        language: str | None,
        status: str,
        coverage_pct: float | None,
        baseline_pct: float | None,
        coverage_gate_pct: float | None,
        coverage_delta_pct: float | None,
        coverage_parser: str | None,
        block_reason: str | None,
    ) -> PanelRunModule:
        now = utc_now()
        values = {
            "run_id": run_id,
            "module_id": module_id,
            "stack": stack,
            "language": language,
            "status": status,
            "coverage_pct": coverage_pct,
            "baseline_pct": baseline_pct,
            "coverage_gate_pct": coverage_gate_pct,
            "coverage_delta_pct": coverage_delta_pct,
            "coverage_parser": coverage_parser,
            "block_reason": block_reason,
            "created_at": now,
            "updated_at": now,
        }
        statement = build_upsert(
            self.session,
            PanelRunModule.__table__,
            values,
            index_elements=["run_id", "module_id"],
            update_columns=[
                "stack",
                "language",
                "status",
                "coverage_pct",
                "baseline_pct",
                "coverage_gate_pct",
                "coverage_delta_pct",
                "coverage_parser",
                "block_reason",
                "updated_at",
            ],
        )
        self.session.execute(statement)
        return self.session.execute(
            select(PanelRunModule).where(
                PanelRunModule.run_id == run_id, PanelRunModule.module_id == module_id
            )
        ).scalar_one()

    def list_for_run(self, run_id: int) -> list[PanelRunModule]:
        return list(
            self.session.execute(
                select(PanelRunModule)
                .where(PanelRunModule.run_id == run_id)
                .order_by(PanelRunModule.module_id.asc())
            ).scalars()
        )
