from __future__ import annotations

import shlex
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    id: str
    label: str
    module: str | None = None
    kind: Literal["build", "lint", "typecheck", "test", "coverage", "custom"] = "custom"
    command: str
    status: str
    exit_code: int
    duration_sec: float
    metrics: dict[str, float] = Field(default_factory=dict)
    gate_target: float | None = None
    stdout_tail: list[str] = Field(default_factory=list)
    stderr_tail: list[str] = Field(default_factory=list)


class RunReport(BaseModel):
    project_name: str
    status: str
    config_path: str
    used_config_file: bool
    strict: bool
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    run_file: str
    checks: list[CheckResult]

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [check for check in self.checks if check.status != "pass"]


class BaselineCheck(BaseModel):
    id: str
    label: str
    module: str | None = None
    kind: Literal["build", "lint", "typecheck", "test", "coverage", "custom"] = "custom"
    command: str
    status: str
    exit_code: int
    metrics: dict[str, float] = Field(default_factory=dict)


class BaselineRecord(BaseModel):
    module: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_created_at: str
    source_run_file: str
    thresholds: dict[str, float] = Field(default_factory=dict)
    checks: list[BaselineCheck] = Field(default_factory=list)


class FileSample(BaseModel):
    path: str
    content: str


class RepoSnapshot(BaseModel):
    root: str
    tree: list[str]
    files: list[FileSample]


class ScanCheckSuggestion(BaseModel):
    id: str
    argv: list[str] | None = None
    run: str | None = None
    cwd: str | None = None

    def resolved_argv(self) -> list[str] | None:
        if self.argv:
            return self.argv
        if self.run:
            return shlex.split(self.run)
        return None


class ScanModuleSuggestion(BaseModel):
    name: str
    path: str
    language: str
    frameworks: list[str] = Field(default_factory=list)
    confidence: float
    evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[ScanCheckSuggestion] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ScanReport(BaseModel):
    project_name: str
    project_type: str
    summary: str
    modules: list[ScanModuleSuggestion] = Field(default_factory=list)
    global_notes: list[str] = Field(default_factory=list)
    provider: str | None = None
    llm_model: str | None = None
