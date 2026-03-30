from __future__ import annotations

import json
from urllib import request

from agentshield_cli.config import NotifyConfig
from agentshield_cli.models import RunReport


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


def send_webhook(report: RunReport, notify: NotifyConfig) -> bool:
    webhook_url = notify.resolved_webhook_url()
    if not webhook_url or not should_send_webhook(report, notify):
        return False

    payload = {
        "project_name": report.project_name,
        "status": report.status,
        "created_at": report.created_at,
        "run_file": report.run_file,
        "failed_checks": [check.id for check in report.failed_checks],
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=notify.timeout_sec):
        return True
