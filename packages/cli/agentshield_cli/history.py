from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from agentshield_cli.models import CheckResult, RunReport


def module_name_from_label(label: str) -> str:
    if " - " not in label:
        return "root"
    return label.split(" - ", 1)[0].strip() or "root"


def group_checks_by_module(report: RunReport) -> OrderedDict[str, list[CheckResult]]:
    grouped: OrderedDict[str, list[CheckResult]] = OrderedDict()
    for check in report.checks:
        module_name = module_name_from_label(check.label)
        grouped.setdefault(module_name, []).append(check)
    return grouped


def summarize_checks(checks: list[CheckResult]) -> dict[str, int | str]:
    total = len(checks)
    passed = sum(1 for check in checks if check.status == "pass")
    failed = total - passed
    status = "pass" if failed == 0 else "fail"
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "status": status,
    }


def load_run_report(run_file: Path) -> RunReport:
    return RunReport.model_validate_json(run_file.read_text(encoding="utf-8"))


def latest_run_report(run_dir: Path) -> tuple[RunReport, Path]:
    latest_path = run_dir / "latest.json"
    if not latest_path.exists():
        msg = f"No AgentShield run history found in `{run_dir}`."
        raise FileNotFoundError(msg)
    return load_run_report(latest_path), latest_path


def list_run_reports(run_dir: Path, limit: int) -> list[tuple[RunReport, Path]]:
    if limit <= 0:
        return []
    if not run_dir.exists():
        return []
    run_files = sorted(
        (
            path
            for path in run_dir.glob("*.json")
            if path.name != "latest.json"
        ),
        reverse=True,
    )
    selected = run_files[:limit]
    return [(load_run_report(path), path) for path in selected]
