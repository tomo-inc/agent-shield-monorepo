from __future__ import annotations

import json
import re
from pathlib import Path

from agentshield_cli.coverage import DEFAULT_LINE_COVERAGE_GATE
from agentshield_cli.history import group_checks_by_module, summarize_checks
from agentshield_cli.models import BaselineCheck, BaselineRecord, CheckResult, RunReport


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def baseline_path_for_module(module: str, baseline_dir: Path) -> Path:
    return baseline_dir / f"{_slug(module)}.json"


def load_baseline(module: str, baseline_dir: Path) -> BaselineRecord | None:
    path = baseline_path_for_module(module, baseline_dir)
    if not path.exists():
        return None
    return BaselineRecord.model_validate_json(path.read_text(encoding="utf-8"))


def _baseline_checks(checks: list[CheckResult]) -> list[BaselineCheck]:
    return [
        BaselineCheck(
            id=check.id,
            label=check.label,
            module=check.module,
            kind=check.kind,
            command=check.command,
            status=check.status,
            exit_code=check.exit_code,
            metrics=check.metrics,
        )
        for check in checks
    ]


def _coverage_thresholds(checks: list[CheckResult]) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for check in checks:
        if check.kind != "coverage":
            continue
        for metric, value in check.metrics.items():
            thresholds[metric] = value
    return thresholds


def build_baseline_record(report: RunReport, module: str, checks: list[CheckResult]) -> BaselineRecord:
    return BaselineRecord(
        module=module,
        source_created_at=report.created_at,
        source_run_file=report.run_file,
        thresholds=_coverage_thresholds(checks),
        checks=_baseline_checks(checks),
    )


def write_baseline(record: BaselineRecord, baseline_dir: Path) -> Path:
    baseline_dir.mkdir(parents=True, exist_ok=True)
    path = baseline_path_for_module(record.module, baseline_dir)
    path.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return path


def update_baselines(
    report: RunReport,
    *,
    baseline_dir: Path,
    module_filter: str | None = None,
) -> list[Path]:
    grouped = group_checks_by_module(report)
    target_modules = [module_filter] if module_filter else list(grouped.keys())
    written_paths: list[Path] = []
    for module in target_modules:
        checks = grouped.get(module)
        if not checks:
            msg = f"Module `{module}` was not present in run `{report.run_file}`."
            raise ValueError(msg)
        record = build_baseline_record(report, module, checks)
        written_paths.append(write_baseline(record, baseline_dir))
    return written_paths


def ensure_initial_baselines(report: RunReport, baseline_dir: Path) -> list[Path]:
    grouped = group_checks_by_module(report)
    written_paths: list[Path] = []
    for module, checks in grouped.items():
        if load_baseline(module, baseline_dir) is not None:
            continue
        record = build_baseline_record(report, module, checks)
        written_paths.append(write_baseline(record, baseline_dir))
    return written_paths


def summarize_baseline(record: BaselineRecord | None) -> dict[str, int | str] | None:
    if record is None:
        return None
    checks = [
        CheckResult(
            id=check.id,
            label=check.label,
            module=check.module,
            kind=check.kind,
            command=check.command,
            status=check.status,
            exit_code=check.exit_code,
            duration_sec=0.0,
            metrics=check.metrics,
            stdout_tail=[],
            stderr_tail=[],
        )
        for check in record.checks
    ]
    return summarize_checks(checks)


def apply_baseline_gates(report: RunReport, baseline_dir: Path) -> RunReport:
    grouped = group_checks_by_module(report)
    for module, checks in grouped.items():
        baseline = load_baseline(module, baseline_dir)
        if baseline is None or not baseline.thresholds:
            continue
        for check in checks:
            if check.kind != "coverage":
                continue
            for metric, value in check.metrics.items():
                threshold = baseline.thresholds.get(metric)
                if threshold is None:
                    continue
                current_gate = (
                    check.gate_target
                    if check.gate_target is not None
                    else DEFAULT_LINE_COVERAGE_GATE
                )
                effective_threshold = max(current_gate, threshold)
                check.gate_target = effective_threshold
                if value + 1e-9 < effective_threshold:
                    check.status = "fail"
                    message = (
                        f"coverage {metric} {value:.1f}% below gate >= {effective_threshold:.1f}%"
                    )
                    if message not in check.stderr_tail:
                        check.stderr_tail.append(message)
                else:
                    check.status = "pass"
    report.status = "pass" if all(check.status == "pass" for check in report.checks) else "fail"
    return report
