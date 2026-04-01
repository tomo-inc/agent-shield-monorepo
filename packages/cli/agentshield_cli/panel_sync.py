from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

from agentshield_cli.baseline import load_baseline
from agentshield_cli.check_details import select_failure_reason
from agentshield_cli.config import AgentShieldConfig
from agentshield_cli.history import module_name_from_label
from agentshield_cli.models import CheckResult, RunReport

PANEL_CHECKERS = {"build", "lint", "typecheck", "test", "coverage"}


@dataclass(frozen=True)
class PanelSettings:
    base_url: str
    token: str | None
    timeout_sec: float


class PanelSyncError(RuntimeError):
    pass


def load_panel_settings() -> PanelSettings | None:
    base_url = os.getenv("AGENTSHIELD_PANEL_BASE_URL")
    if not base_url:
        return None
    timeout_raw = os.getenv("AGENTSHIELD_PANEL_TIMEOUT_SEC", "5")
    try:
        timeout_sec = float(timeout_raw)
    except ValueError as exc:
        raise PanelSyncError(f"invalid AGENTSHIELD_PANEL_TIMEOUT_SEC: {timeout_raw}") from exc
    if timeout_sec <= 0:
        raise PanelSyncError("AGENTSHIELD_PANEL_TIMEOUT_SEC must be greater than 0")
    return PanelSettings(
        base_url=base_url.rstrip("/"),
        token=os.getenv("AGENTSHIELD_PANEL_TOKEN"),
        timeout_sec=timeout_sec,
    )


def sync_project_register(config: AgentShieldConfig, onboarding_status: str) -> bool:
    payload = build_project_register_payload(config, onboarding_status)
    return _post("project register", "/api/v1/panel/projects/register", payload)


def sync_baselines(
    config: AgentShieldConfig,
    *,
    baseline_dir: Path,
    updated_at: datetime,
    module_names: list[str] | None = None,
) -> bool:
    payload = build_baseline_upload_payload(
        config,
        baseline_dir=baseline_dir,
        updated_at=updated_at,
        module_names=module_names,
    )
    if payload is None:
        print("Panel sync: baselines skipped (no coverage baseline data)")
        return False
    return _post("baselines", "/api/v1/panel/baselines", payload)


def sync_run(config: AgentShieldConfig, report: RunReport, *, baseline_dir: Path) -> bool:
    payload = build_run_upload_payload(config, report, baseline_dir=baseline_dir)
    return _post("run", "/api/v1/panel/runs", payload)


def build_project_register_payload(config: AgentShieldConfig, onboarding_status: str) -> dict[str, object]:
    modules = [{"module_name": module_name, "stack": None, "language": None} for module_name in _config_modules(config)]
    return {
        "project_key": config.project.name,
        "project_name": config.project.name,
        "repo_path": str(config.project_root),
        "preset": "custom",
        "onboarding_status": onboarding_status,
        "modules": modules,
    }


def build_baseline_upload_payload(
    config: AgentShieldConfig,
    *,
    baseline_dir: Path,
    updated_at: datetime,
    module_names: list[str] | None = None,
) -> dict[str, object] | None:
    modules: list[dict[str, object]] = []
    target_modules = module_names or _config_modules(config)
    for module_name in target_modules:
        baseline = load_baseline(module_name, baseline_dir)
        if baseline is None:
            continue
        baseline_pct = baseline.thresholds.get("line")
        if not isinstance(baseline_pct, (float, int)):
            continue
        modules.append({"module_name": module_name, "baseline_pct": float(baseline_pct)})
    if not modules:
        return None
    return {
        "project_key": config.project.name,
        "updated_at": updated_at.astimezone(timezone.utc).isoformat(),
        "modules": modules,
    }


def build_run_upload_payload(config: AgentShieldConfig, report: RunReport, *, baseline_dir: Path) -> dict[str, object]:
    modules_payload: list[dict[str, object]] = []
    for module_name, checks in _group_report_checks(report).items():
        coverage_check = next((check for check in checks if check.kind == "coverage"), None)
        baseline = load_baseline(module_name, baseline_dir)
        baseline_pct_raw = baseline.thresholds.get("line") if baseline is not None else None
        baseline_pct = float(baseline_pct_raw) if isinstance(baseline_pct_raw, (float, int)) else None
        coverage_pct_raw = coverage_check.metrics.get("line") if coverage_check is not None else None
        coverage_pct = float(coverage_pct_raw) if isinstance(coverage_pct_raw, (float, int)) else None
        coverage_gate_pct = coverage_check.gate_target if coverage_check and coverage_check.gate_target is not None else None
        coverage_delta_pct = None
        if coverage_pct is not None and baseline_pct is not None:
            coverage_delta_pct = round(coverage_pct - baseline_pct, 4)
        checker_results = [
            {
                "checker": check.kind,
                "status": check.status,
                "detail": _check_detail(check, config.project_root),
                "duration_sec": check.duration_sec,
            }
            for check in checks
            if check.kind in PANEL_CHECKERS
        ]
        modules_payload.append(
            {
                "module_name": module_name,
                "stack": None,
                "language": None,
                "status": _module_status(checks),
                "coverage_pct": coverage_pct,
                "baseline_pct": baseline_pct,
                "coverage_gate_pct": coverage_gate_pct,
                "coverage_delta_pct": coverage_delta_pct,
                "coverage_parser": None,
                "block_reason": None,
                "checker_results": checker_results,
            }
        )
    return {
        "project_key": config.project.name,
        "run_key": Path(report.run_file).name,
        "source": None,
        "git_ref": None,
        "git_sha": None,
        "triggered_by": None,
        "started_at": None,
        "finished_at": _parse_report_time(report.created_at).isoformat(),
        "duration_sec": None,
        "strict_mode": report.strict,
        "status": report.status,
        "block_reason": None,
        "modules": modules_payload,
    }


def _post(label: str, path: str, payload: dict[str, object]) -> bool:
    try:
        settings = load_panel_settings()
    except PanelSyncError as exc:
        print(f"Panel sync failed: {exc}")
        return False
    if settings is None:
        print("Panel sync: skipped")
        return False

    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.token:
        headers["Authorization"] = f"Bearer {settings.token}"
    req = request.Request(
        f"{settings.base_url}{path}",
        data=body,
        method="POST",
        headers=headers,
    )
    try:
        with request.urlopen(req, timeout=settings.timeout_sec) as response:
            response.read()
    except error.HTTPError as exc:
        detail = _read_http_error(exc)
        print(f"Panel sync failed: {label} http {exc.code} {detail}".rstrip())
        return False
    except (error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        reason = getattr(exc, "reason", str(exc))
        print(f"Panel sync failed: {label} {reason}")
        return False

    print(f"Panel sync: {label} ok")
    return True


def _read_http_error(exc: error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return ""
    detail = payload.get("detail")
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str):
            return message
    return ""


def _config_modules(config: AgentShieldConfig) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for check in config.checks:
        module_name = _check_module_name(check)
        if module_name in seen:
            continue
        seen.add(module_name)
        modules.append(module_name)
    return modules


def _group_report_checks(report: RunReport) -> dict[str, list[CheckResult]]:
    grouped: dict[str, list[CheckResult]] = {}
    for check in report.checks:
        module_name = _check_module_name(check)
        grouped.setdefault(module_name, []).append(check)
    return grouped


def _check_module_name(check: CheckResult | object) -> str:
    module = getattr(check, "module", None)
    if isinstance(module, str) and module.strip():
        return module
    label = getattr(check, "label", "")
    return module_name_from_label(label)


def _module_status(checks: list[CheckResult]) -> str:
    statuses = {check.status for check in checks if check.kind in PANEL_CHECKERS}
    if "timeout" in statuses:
        return "timeout"
    if any(status != "pass" for status in statuses):
        return "fail"
    return "pass"


def _check_detail(check: CheckResult, project_root: Path | None = None) -> str | None:
    if check.status == "pass":
        if check.stdout_tail:
            return check.stdout_tail[-1]
        if check.stderr_tail:
            return check.stderr_tail[-1]
        return None
    return select_failure_reason(check, project_root=project_root)


def _parse_report_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
