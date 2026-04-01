from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import re
import subprocess
import time
from collections import OrderedDict
from pathlib import Path
from typing import Callable

from agentshield_cli.baseline import apply_baseline_gates
from agentshield_cli.check_details import missing_step_message
from agentshield_cli.config import AgentShieldConfig, CheckConfig
from agentshield_cli.coverage import (
    DEFAULT_LINE_COVERAGE_GATE,
    coverage_gate_message,
    parse_coverage_metrics,
)
from agentshield_cli.models import CheckResult, RunReport
from agentshield_cli.notifier import send_webhook

REQUIRED_CHECK_KINDS = ("build", "lint", "typecheck", "test", "coverage")


def _normalize_output(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _tail_lines(value: str, size: int = 10) -> list[str]:
    lines = [line.rstrip() for line in value.splitlines() if line.strip()]
    return lines[-size:]


def _group_checks_by_module(checks: list[CheckConfig]) -> OrderedDict[str, list[CheckConfig]]:
    grouped: OrderedDict[str, list[CheckConfig]] = OrderedDict()
    for check in checks:
        module_name = check.module or check.label.split(" - ", 1)[0]
        grouped.setdefault(module_name, []).append(check)
    return grouped


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _missing_required_results(module_name: str, checks: list[CheckConfig], project_root: Path) -> list[CheckResult]:
    existing_kinds = {check.kind for check in checks}
    missing_results: list[CheckResult] = []
    for kind in REQUIRED_CHECK_KINDS:
        if kind in existing_kinds:
            continue
        missing_results.append(
            CheckResult(
                id=f"{_slug(module_name)}-{kind}-missing",
                label=f"{module_name} - {kind}",
                module=module_name,
                kind=kind,
                command="(missing configuration)",
                status="fail",
                exit_code=2,
                duration_sec=0.0,
                metrics={},
                stdout_tail=[],
                stderr_tail=[missing_step_message(module_name, kind, project_root)],
            )
        )
    return missing_results


def _emit_progress(
    result: CheckResult,
    progress_callback: Callable[[CheckResult], None] | None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(result)


def _run_module_checks(
    checks: list[CheckConfig],
    project_root: Path,
    *,
    progress_callback: Callable[[CheckResult], None] | None = None,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in checks:
        result = run_single_check(check, project_root)
        results.append(result)
        _emit_progress(result, progress_callback)
    return results


def run_single_check(check: CheckConfig, project_root: Path) -> CheckResult:
    started = time.monotonic()
    command_display = check.command_display()
    cwd = project_root / check.cwd if check.cwd else project_root
    module_name = check.module
    coverage_path = cwd / check.coverage_file if check.coverage_file else None
    gate_target: float | None = None
    if coverage_path is not None:
        coverage_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        argv = check.resolved_argv()
        if argv is not None:
            completed = subprocess.run(
                argv,
                shell=False,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=check.timeout_sec,
                check=False,
            )
        else:
            if check.run is None:
                msg = f"Check `{check.id}` does not define a runnable command."
                raise ValueError(msg)
            completed = subprocess.run(
                check.run,
                shell=True,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=check.timeout_sec,
                check=False,
            )
        status = "pass" if completed.returncode == 0 else "fail"
        metrics: dict[str, float] = {}
        stderr_tail = _tail_lines(completed.stderr)
        if status == "pass" and check.coverage_parser and coverage_path is not None:
            try:
                metrics = parse_coverage_metrics(check.coverage_parser, coverage_path)
                gate_target = DEFAULT_LINE_COVERAGE_GATE
                line_coverage = metrics.get("line")
                if line_coverage is not None and line_coverage + 1e-9 < DEFAULT_LINE_COVERAGE_GATE:
                    status = "fail"
                    stderr_tail.append(
                        coverage_gate_message("line", line_coverage, DEFAULT_LINE_COVERAGE_GATE)
                    )
            except (FileNotFoundError, ValueError) as exc:
                status = "fail"
                stderr_tail.append(str(exc))
        return CheckResult(
            id=check.id,
            label=check.label,
            module=module_name,
            kind=check.kind,
            command=command_display,
            status=status,
            exit_code=completed.returncode,
            duration_sec=round(time.monotonic() - started, 2),
            metrics=metrics,
            gate_target=gate_target,
            stdout_tail=_tail_lines(completed.stdout),
            stderr_tail=stderr_tail,
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            id=check.id,
            label=check.label,
            module=module_name,
            kind=check.kind,
            command=command_display,
            status="timeout",
            exit_code=124,
            duration_sec=round(time.monotonic() - started, 2),
            metrics={},
            stdout_tail=_tail_lines(_normalize_output(exc.stdout or "")),
            stderr_tail=_tail_lines(_normalize_output(exc.stderr or "")),
        )
    except FileNotFoundError as exc:
        missing_command = exc.filename or command_display or check.id
        return CheckResult(
            id=check.id,
            label=check.label,
            module=module_name,
            kind=check.kind,
            command=command_display,
            status="fail",
            exit_code=127,
            duration_sec=round(time.monotonic() - started, 2),
            metrics={},
            stdout_tail=[],
            stderr_tail=[f"command not found: {missing_command}"],
        )
    except ValueError as exc:
        return CheckResult(
            id=check.id,
            label=check.label,
            module=module_name,
            kind=check.kind,
            command=command_display,
            status="fail",
            exit_code=2,
            duration_sec=round(time.monotonic() - started, 2),
            metrics={},
            stdout_tail=[],
            stderr_tail=[str(exc)],
        )


def write_run_report(report: RunReport, run_dir: Path) -> RunReport:
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = report.created_at.replace(":", "-")
    target = run_dir / f"{timestamp}.json"
    serialized = report.model_dump(mode="json")
    serialized["run_file"] = str(target)
    target.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    latest = run_dir / "latest.json"
    latest.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    return RunReport.model_validate(serialized)


def run_checks(
    config: AgentShieldConfig,
    *,
    config_path: Path,
    used_config_file: bool,
    strict: bool,
    run_dir: Path,
    baseline_dir: Path | None = None,
    send_notifications: bool = True,
    progress_callback: Callable[[CheckResult], None] | None = None,
) -> tuple[RunReport, bool]:
    project_root = config.project_root
    grouped_all_checks = _group_checks_by_module(config.checks)
    enabled_checks = [check for check in config.checks if check.enabled]
    if enabled_checks:
        grouped_checks = _group_checks_by_module(enabled_checks)
        max_workers = min(len(grouped_checks), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                module_name: executor.submit(
                    _run_module_checks,
                    checks,
                    project_root,
                    progress_callback=progress_callback,
                )
                for module_name, checks in grouped_checks.items()
            }
            results = []
            for module_name, future in futures.items():
                module_checks = grouped_all_checks.get(module_name, grouped_checks[module_name])
                results.extend(future.result())
                missing_results = _missing_required_results(module_name, module_checks, project_root)
                results.extend(missing_results)
                for result in missing_results:
                    _emit_progress(result, progress_callback)
    else:
        results = []
    status = "pass" if all(result.status == "pass" for result in results) else "fail"
    report = RunReport(
        project_name=config.project.name,
        status=status,
        config_path=str(config_path),
        used_config_file=used_config_file,
        strict=strict,
        run_file="",
        checks=results,
    )
    if baseline_dir is not None:
        report = apply_baseline_gates(report, baseline_dir)
    report = write_run_report(report, run_dir)
    webhook_sent = (
        send_webhook(report, config.notify, project_root=project_root) if send_notifications else False
    )
    return report, webhook_sent
