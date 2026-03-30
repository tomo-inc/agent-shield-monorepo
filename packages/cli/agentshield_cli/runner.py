from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import time
from pathlib import Path

from agentshield_cli.config import AgentShieldConfig, CheckConfig
from agentshield_cli.models import CheckResult, RunReport
from agentshield_cli.notifier import send_webhook


def _normalize_output(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _tail_lines(value: str, size: int = 10) -> list[str]:
    lines = [line.rstrip() for line in value.splitlines() if line.strip()]
    return lines[-size:]


def run_single_check(check: CheckConfig, project_root: Path) -> CheckResult:
    started = time.monotonic()
    command_display = check.command_display()
    cwd = project_root / check.cwd if check.cwd else project_root
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
        return CheckResult(
            id=check.id,
            label=check.label,
            command=command_display,
            status=status,
            exit_code=completed.returncode,
            duration_sec=round(time.monotonic() - started, 2),
            stdout_tail=_tail_lines(completed.stdout),
            stderr_tail=_tail_lines(completed.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        return CheckResult(
            id=check.id,
            label=check.label,
            command=command_display,
            status="timeout",
            exit_code=124,
            duration_sec=round(time.monotonic() - started, 2),
            stdout_tail=_tail_lines(_normalize_output(exc.stdout or "")),
            stderr_tail=_tail_lines(_normalize_output(exc.stderr or "")),
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
    send_notifications: bool = True,
) -> tuple[RunReport, bool]:
    project_root = config.project_root
    enabled_checks = [check for check in config.checks if check.enabled]
    if enabled_checks:
        max_workers = min(len(enabled_checks), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(run_single_check, check, project_root)
                for check in enabled_checks
            ]
            results = [future.result() for future in futures]
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
    report = write_run_report(report, run_dir)
    webhook_sent = send_webhook(report, config.notify) if send_notifications else False
    return report, webhook_sent
