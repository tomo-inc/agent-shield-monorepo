from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Double, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


JsonType = JSONB().with_variant(JSON(), "sqlite")
BigIntType = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    pass


class PanelProject(Base):
    __tablename__ = "panel_projects"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    project_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    repo_path: Mapped[str] = mapped_column(String, nullable=False)
    preset: Mapped[str] = mapped_column(String, nullable=False)
    onboarding_status: Mapped[str] = mapped_column(String, nullable=False)
    commands_json: Mapped[dict[str, str] | None] = mapped_column(JsonType)
    thresholds_json: Mapped[dict[str, Any] | None] = mapped_column(JsonType)
    timeouts_json: Mapped[dict[str, int] | None] = mapped_column(JsonType)
    notify_json: Mapped[dict[str, str] | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PanelModule(Base):
    __tablename__ = "panel_modules"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False
    )
    module_name: Mapped[str] = mapped_column(String, nullable=False)
    stack: Mapped[str | None] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PanelBaseline(Base):
    __tablename__ = "panel_baselines"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_modules.id", ondelete="CASCADE"), nullable=False
    )
    baseline_pct: Mapped[float | None] = mapped_column(Double)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PanelRun(Base):
    __tablename__ = "panel_runs"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_projects.id", ondelete="CASCADE"), nullable=False
    )
    run_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source: Mapped[str | None] = mapped_column(String)
    git_ref: Mapped[str | None] = mapped_column(String)
    git_sha: Mapped[str | None] = mapped_column(String)
    triggered_by: Mapped[str | None] = mapped_column(String)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[float | None] = mapped_column(Double)
    strict_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String, nullable=False)
    block_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PanelRunModule(Base):
    __tablename__ = "panel_run_modules"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_runs.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_modules.id", ondelete="CASCADE"), nullable=False
    )
    stack: Mapped[str | None] = mapped_column(String)
    language: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    coverage_pct: Mapped[float | None] = mapped_column(Double)
    baseline_pct: Mapped[float | None] = mapped_column(Double)
    coverage_gate_pct: Mapped[float | None] = mapped_column(Double)
    coverage_delta_pct: Mapped[float | None] = mapped_column(Double)
    coverage_parser: Mapped[str | None] = mapped_column(String)
    block_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class PanelCheckerResult(Base):
    __tablename__ = "panel_checker_results"

    id: Mapped[int] = mapped_column(BigIntType, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_runs.id", ondelete="CASCADE"), nullable=False
    )
    run_module_id: Mapped[int] = mapped_column(
        BigIntType, ForeignKey("panel_run_modules.id", ondelete="CASCADE"), nullable=False
    )
    checker: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    duration_sec: Mapped[float | None] = mapped_column(Double)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


Index("idx_panel_modules_project_module", PanelModule.project_id, PanelModule.module_name, unique=True)
Index("idx_panel_baselines_project_module", PanelBaseline.project_id, PanelBaseline.module_id, unique=True)
Index("idx_panel_runs_project_finished_at", PanelRun.project_id, PanelRun.finished_at, PanelRun.id)
Index("idx_panel_run_modules_run_module", PanelRunModule.run_id, PanelRunModule.module_id, unique=True)
Index("idx_panel_run_modules_run_id", PanelRunModule.run_id)
Index("idx_panel_checker_results_unique", PanelCheckerResult.run_module_id, PanelCheckerResult.checker, unique=True)
Index("idx_panel_checker_results_run_id", PanelCheckerResult.run_id)
