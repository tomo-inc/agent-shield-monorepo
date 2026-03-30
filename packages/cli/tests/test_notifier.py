from __future__ import annotations

from pathlib import Path

from agentshield_cli.config import NotifyConfig
from agentshield_cli.models import CheckResult, RunReport
from agentshield_cli.notifier import send_webhook, should_send_webhook


class _DummyResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_should_send_webhook_for_failure() -> None:
    report = RunReport(
        project_name="demo",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file=".qa-agent/runs/demo.json",
        checks=[
            CheckResult(
                id="lint",
                label="Lint",
                command="pnpm lint",
                status="fail",
                exit_code=1,
                duration_sec=1.0,
            )
        ],
    )

    assert should_send_webhook(report, NotifyConfig(enabled=True, webhook_url="https://example.com")) is True


def test_send_webhook_posts_json(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse()

    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="demo",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[],
    )
    sent = send_webhook(
        report,
        NotifyConfig(enabled=True, webhook_url="https://example.com/hook", timeout_sec=3),
    )

    assert sent is True
    assert captured["url"] == "https://example.com/hook"
    assert "\"status\": \"fail\"" in captured["body"]
    assert captured["timeout"] == "3"
