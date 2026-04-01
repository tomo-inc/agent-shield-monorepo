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


def test_send_webhook_uses_dependency_drift_reason_when_project_root_is_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, str] = {}
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        '{"name":"demo","packageManager":"pnpm@10.11.0"}',
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        '{"name":"@demo/web","devDependencies":{"happy-dom":"^20.8.9"}}',
        encoding="utf-8",
    )

    def fake_urlopen(req, timeout):
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
        checks=[
            CheckResult(
                id="apps-web-test",
                label="apps/web - test",
                module="apps/web",
                kind="test",
                command="pnpm run test",
                status="fail",
                exit_code=1,
                duration_sec=0.2,
                stdout_tail=["MISSING DEPENDENCY  Cannot find dependency 'happy-dom'"],
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
        project_root=tmp_path,
    )

    assert sent is True
    assert "`happy-dom` is declared in `apps/web/package.json`" in captured["body"]


def test_send_webhook_prefers_real_error_over_warning_reason(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="source-agent",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[
            CheckResult(
                id="apps-api-typecheck",
                label="apps/api - typecheck",
                module="apps/api",
                kind="typecheck",
                command="uv run --extra dev mypy src",
                status="fail",
                exit_code=1,
                duration_sec=5.43,
                stdout_tail=[
                    (
                        "src/source_agent/services/pipeline.py:294: error: Argument "
                        "\"provider_params\" has incompatible type"
                    ),
                    "Found 1 error in 1 file (checked 21 source files)",
                ],
                stderr_tail=[
                    (
                        "warning: `VIRTUAL_ENV=/Users/admin/tomo_project/agent-shield-monorepo/packages/cli/.venv` "
                        "does not match the project environment path `.venv` and will be ignored"
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
    assert "pipeline.py:294: error" in captured["body"]
    assert "does not match the project environment path" not in captured["body"]


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


def test_send_webhook_uses_specific_missing_step_reason_when_available(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req, timeout):
        captured["body"] = req.data.decode("utf-8")
        captured["timeout"] = str(timeout)
        return _DummyResponse('{"code":0,"msg":"success"}')

    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (module_root / "package.json").write_text(
        """
        {
          "name": "@demo/web",
          "scripts": {
            "build": "next build",
            "lint": "eslint . --max-warnings=0",
            "typecheck": "tsc --noEmit",
            "test": "echo \\"No web tests yet\\""
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agentshield_cli.notifier.request.urlopen", fake_urlopen)
    report = RunReport(
        project_name="source-agent",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        run_file=str(Path(".qa-agent/runs/demo.json")),
        checks=[
            CheckResult(
                id="apps-web-test-missing",
                label="apps/web - test",
                module="apps/web",
                kind="test",
                command="(missing configuration)",
                status="fail",
                exit_code=2,
                duration_sec=0.0,
                stderr_tail=[
                    (
                        "`apps/web/package.json` defines `test` as a placeholder script "
                        "(`echo \"No web tests yet\"`), so AgentShield treated it as missing real test coverage."
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
    assert "placeholder script" in captured["body"]
