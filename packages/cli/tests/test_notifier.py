from __future__ import annotations

from pathlib import Path

from agentshield_cli.config import NotifyConfig
from agentshield_cli.models import CheckResult, RunReport
from agentshield_cli.notifier import send_webhook, should_send_webhook


class _DummyResponse:
    def __init__(self, body: str = "") -> None:
        self._body = body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


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


def test_should_send_webhook_for_success_when_enabled() -> None:
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file=".qa-agent/runs/demo.json",
        checks=[],
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


def test_send_webhook_posts_lark_text_message(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

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
        NotifyConfig(
            enabled=True,
            webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/demo",
            timeout_sec=3,
        ),
    )

    assert sent is True
    assert captured["url"] == "https://open.larksuite.com/open-apis/bot/v2/hook/demo"
    assert "\"msg_type\": \"text\"" in captured["body"]
    assert "AgentShield FAIL" in captured["body"]
    assert "reason" not in captured["body"]
    assert captured["timeout"] == "3"


def test_send_webhook_returns_false_for_lark_error_body(monkeypatch) -> None:
    def fake_urlopen(req, timeout):
        del req, timeout
        return _DummyResponse('{"code":19022,"msg":"invalid request"}')

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
        NotifyConfig(
            enabled=True,
            webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/demo",
            timeout_sec=3,
        ),
    )

    assert sent is False


def test_send_webhook_lark_message_includes_check_summary(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="chain_abs_cubist",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[
            CheckResult(
                id="merchant-lint",
                label="merchant - lint",
                module="merchant",
                kind="lint",
                command="cargo clippy --bin merchant -- -D warnings",
                status="fail",
                exit_code=101,
                duration_sec=4.99,
                stderr_tail=["error: could not compile `chain_abs_cubist` (lib) due to 32 previous errors"],
            ),
            CheckResult(
                id="merchant-test",
                label="merchant - test",
                module="merchant",
                kind="test",
                command="cargo test --bin merchant",
                status="pass",
                exit_code=0,
                duration_sec=0.40,
            ),
        ],
    )

    sent = send_webhook(
        report,
        NotifyConfig(
            enabled=True,
            webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/demo",
            timeout_sec=3,
        ),
    )

    assert sent is True
    assert "merchant" in captured["body"]
    assert "lint: FAIL (4.99s)" in captured["body"]
    assert "test: PASS (0.40s)" in captured["body"]
    assert "could not compile `chain_abs_cubist`" in captured["body"]
    assert ".qa-agent/runs" not in captured["body"]


def test_send_webhook_does_not_include_reason_for_pass_checks(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="chain_abs_cubist",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[
            CheckResult(
                id="merchant-lint",
                label="merchant - lint",
                module="merchant",
                kind="lint",
                command="cargo clippy --bin merchant",
                status="pass",
                exit_code=0,
                duration_sec=1.10,
                stderr_tail=["note: future-incompat-report"],
            ),
            CheckResult(
                id="merchant-test",
                label="merchant - test",
                module="merchant",
                kind="test",
                command="cargo test --package chain_abs_cubist --bin merchant",
                status="pass",
                exit_code=0,
                duration_sec=1.07,
                stderr_tail=["Running unittests src/bin/merchant.rs"],
            ),
        ],
    )

    sent = send_webhook(
        report,
        NotifyConfig(
            enabled=True,
            webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/demo",
            timeout_sec=3,
        ),
    )

    assert sent is True
    assert "lint: PASS (1.10s)" in captured["body"]
    assert "test: PASS (1.07s)" in captured["body"]
    assert "reason:" not in captured["body"]


def test_send_webhook_uses_customer_facing_missing_step_reason(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="agentpay-sdk-internal",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[
            CheckResult(
                id="relay-coverage-missing",
                label="apps/relay - coverage",
                module="apps/relay",
                kind="coverage",
                command="(missing configuration)",
                status="fail",
                exit_code=2,
                duration_sec=0.0,
                stderr_tail=[
                    (
                        "AgentShield did not generate a `coverage` step for module `apps/relay` "
                        "during setup. This module cannot pass until that step is added. Re-run "
                        "`agentshield init --yes` to scan again, or add the command manually."
                    )
                ],
            )
        ],
    )

    sent = send_webhook(
        report,
        NotifyConfig(
            enabled=True,
            webhook_url="https://open.larksuite.com/open-apis/bot/v2/hook/demo",
            timeout_sec=3,
        ),
    )

    assert sent is True
    assert "apps/relay" in captured["body"]
    assert "coverage: FAIL (0.00s)" in captured["body"]
    assert "did not generate a `coverage` step" in captured["body"]
    assert "missing from `.agentshield/config.yaml`" not in captured["body"]
