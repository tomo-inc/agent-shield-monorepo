from __future__ import annotations

import json
from pathlib import Path
from urllib import parse, request

from agentshield_cli.check_details import select_failure_reason
from agentshield_cli.config import NotifyConfig
from agentshield_cli.history import group_checks_by_module
from agentshield_cli.models import CheckResult, RunReport


LARK_HOST_SUFFIXES = (
    "open.larksuite.com",
    "open.feishu.cn",
)


def should_send_webhook(report: RunReport, notify: NotifyConfig) -> bool:
    if not notify.enabled:
        return False
    if "always" in notify.send_on:
        return True
    if report.status == "fail" and "failure" in notify.send_on:
        return True
    if report.status == "pass" and "success" in notify.send_on:
        return True
    return False


def _is_lark_webhook(webhook_url: str) -> bool:
    hostname = parse.urlparse(webhook_url).hostname or ""
    return any(hostname.endswith(suffix) for suffix in LARK_HOST_SUFFIXES)


def _lark_payload(report: RunReport, project_root: Path | None = None) -> dict[str, object]:
    text = _lark_text(report, project_root=project_root)
    return {
        "msg_type": "text",
        "content": {
            "text": text,
        },
    }


def _generic_payload(report: RunReport) -> dict[str, object]:
    return {
        "project_name": report.project_name,
        "status": report.status,
        "created_at": report.created_at,
        "summary": _lark_text(report),
        "failed_checks": [check.id for check in report.failed_checks],
    }


def _format_check_line(check: CheckResult) -> str:
    parts = [f"{check.kind}: {check.status.upper()} ({check.duration_sec:.2f}s)"]
    if check.kind == "coverage" and "line" in check.metrics:
        line = f"line {check.metrics['line']:.1f}%"
        if check.gate_target is not None:
            line += f" / gate >= {check.gate_target:.1f}%"
        parts.append(line)
    return " | ".join(parts)


def _failure_reason(check: CheckResult, project_root: Path | None = None) -> str | None:
    return select_failure_reason(check, project_root=project_root)


def _lark_text(report: RunReport, project_root: Path | None = None) -> str:
    lines = [f"AgentShield {report.status.upper()} · {report.project_name}"]
    for module, checks in group_checks_by_module(report).items():
        lines.append(f"{module}")
        for check in checks:
            lines.append(f"- {_format_check_line(check)}")
            reason = _failure_reason(check, project_root=project_root)
            if reason:
                lines.append(f"  reason: {reason}")
    return "\n".join(lines)


def _is_lark_success(response_body: bytes) -> bool:
    try:
        payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if payload.get("code") == 0:
        return True
    if payload.get("StatusCode") == 0:
        return True
    return False


def send_webhook(report: RunReport, notify: NotifyConfig, *, project_root: Path | None = None) -> bool:
    webhook_url = notify.resolved_webhook_url()
    if not webhook_url or not should_send_webhook(report, notify):
        return False

    payload = (
        _lark_payload(report, project_root=project_root)
        if _is_lark_webhook(webhook_url)
        else _generic_payload(report)
    )
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=notify.timeout_sec) as response:
        response_body = response.read()
    if _is_lark_webhook(webhook_url):
        return _is_lark_success(response_body)
    return True
