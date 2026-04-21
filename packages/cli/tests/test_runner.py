from __future__ import annotations

import shlex
import sys
from pathlib import Path

from agentshield_cli.config import AgentShieldConfig, CheckConfig, NotifyConfig, ProjectConfig
from agentshield_cli.runner import run_checks


def _passing_module_checks() -> list[CheckConfig]:
    coverage_program = (
        "from pathlib import Path; "
        "Path('coverage.json').write_text('{\"totals\": {\"percent_covered\": 100.0}}', encoding='utf-8')"
    )
    ok = [sys.executable, "-c", "print('ok')"]
    return [
        CheckConfig(id="build", label="mod - build", module="mod", kind="build", argv=ok),
        CheckConfig(id="lint", label="mod - lint", module="mod", kind="lint", argv=ok),
        CheckConfig(id="typecheck", label="mod - typecheck", module="mod", kind="typecheck", argv=ok),
        CheckConfig(id="test", label="mod - test", module="mod", kind="test", argv=ok),
        CheckConfig(
            id="coverage",
            label="mod - coverage",
            module="mod",
            kind="coverage",
            argv=[sys.executable, "-c", coverage_program],
            coverage_parser="coverage.py-json",
            coverage_file="coverage.json",
        ),
    ]


def test_run_checks_writes_report_and_marks_failure(tmp_path: Path) -> None:
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks()
        + [
            CheckConfig(
                id="bad",
                label="mod - custom",
                module="mod",
                kind="custom",
                run="python -c \"raise SystemExit(2)\"",
                timeout_sec=5,
            )
        ],
        notify=NotifyConfig(enabled=False),
    )

    report, webhook_sent = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "fail"
    assert webhook_sent is False
    assert Path(report.run_file).exists()
    assert (tmp_path / ".qa-agent" / "runs" / "latest.json").exists()


def test_run_checks_marks_success(tmp_path: Path) -> None:
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks(),
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=False,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "pass"


def test_run_checks_parses_coverage_metrics_when_command_fails_after_writing_report(tmp_path: Path) -> None:
    coverage_program = (
        "from pathlib import Path; "
        "import sys; "
        "Path('coverage.json').write_text('{\"totals\": {\"percent_covered\": 73.5}}', encoding='utf-8'); "
        "print('tests failed', file=sys.stderr); "
        "raise SystemExit(1)"
    )
    checks = _passing_module_checks()
    checks[-1] = CheckConfig(
        id="coverage",
        label="mod - coverage",
        module="mod",
        kind="coverage",
        argv=[sys.executable, "-c", coverage_program],
        coverage_parser="coverage.py-json",
        coverage_file="coverage.json",
    )
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=checks,
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=False,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    coverage_check = next(check for check in report.checks if check.kind == "coverage")
    assert report.status == "fail"
    assert coverage_check.status == "fail"
    assert coverage_check.exit_code == 1
    assert coverage_check.metrics == {"line": 73.5}
    assert coverage_check.gate_target == 100.0
    assert coverage_check.stderr_tail == ["tests failed"]


def test_run_checks_preserves_shell_semantics_for_run_commands(tmp_path: Path) -> None:
    run_command = (
        f"FLAG=ok {shlex.quote(sys.executable)} -c "
        "'import os, pathlib; pathlib.Path(\"marker.txt\").write_text(os.environ[\"FLAG\"], encoding=\"utf-8\")' "
        f"&& {shlex.quote(sys.executable)} -c 'print(\"done\")'"
    )
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks()
        + [
            CheckConfig(
                id="shell",
                label="mod - custom",
                module="mod",
                kind="custom",
                run=run_command,
                timeout_sec=5,
            )
        ],
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "pass"
    assert (tmp_path / "marker.txt").read_text(encoding="utf-8") == "ok"


def test_run_checks_skips_notifications_when_disabled(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []

    def fake_send_webhook(*args, **kwargs) -> bool:
        calls.append("called")
        return True

    monkeypatch.setattr("agentshield_cli.runner.send_webhook", fake_send_webhook)
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks(),
        notify=NotifyConfig(enabled=True, webhook_url="https://example.com/webhook"),
    )

    report, webhook_sent = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=False,
        run_dir=tmp_path / ".qa-agent" / "runs",
        send_notifications=False,
    )

    assert report.status == "pass"
    assert webhook_sent is False
    assert calls == []


def test_run_checks_marks_missing_command_as_failure(tmp_path: Path) -> None:
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks()
        + [
            CheckConfig(
                id="missing",
                label="mod - custom",
                module="mod",
                kind="custom",
                argv=["definitely-not-a-real-command"],
                timeout_sec=5,
            )
        ],
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "fail"
    assert any(check.status == "fail" for check in report.checks)
    assert any(check.exit_code == 127 for check in report.checks)
    assert any(
        check.stderr_tail == ["command not found: definitely-not-a-real-command"]
        for check in report.checks
    )


def test_run_checks_fails_when_required_checks_are_missing(tmp_path: Path) -> None:
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=[
            CheckConfig(
                id="test",
                label="merchant - test",
                module="merchant",
                kind="test",
                argv=[sys.executable, "-c", "print('ok')"],
            )
        ],
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "fail"
    missing_kinds = {check.kind for check in report.checks if check.command == "(missing configuration)"}
    assert missing_kinds == {"build", "lint", "typecheck", "coverage"}
    missing_coverage = next(check for check in report.checks if check.kind == "coverage")
    assert missing_coverage.stderr_tail == [
        (
            "AgentShield did not generate a `coverage` step for module `merchant` during setup. "
            "This module cannot pass until that step is added. Re-run `agentshield init --yes` "
            "to scan again, or add the command manually."
        )
    ]


def test_run_checks_allows_disabled_required_check_without_missing_failure(tmp_path: Path) -> None:
    checks = _passing_module_checks()
    checks[-1] = checks[-1].model_copy(update={"enabled": False})
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=checks,
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    assert report.status == "pass"
    assert not any(check.command == "(missing configuration)" for check in report.checks)
    assert {check.kind for check in report.checks} == {"build", "lint", "typecheck", "test"}


def test_run_checks_emits_progress_for_each_result(tmp_path: Path) -> None:
    progress: list[str] = []
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=_passing_module_checks(),
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=False,
        run_dir=tmp_path / ".qa-agent" / "runs",
        progress_callback=lambda result: progress.append(result.id),
    )

    assert report.status == "pass"
    assert progress == ["build", "lint", "typecheck", "test", "coverage"]


def test_run_checks_uses_specific_missing_reason_from_project_facts(tmp_path: Path) -> None:
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
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=[
            CheckConfig(
                id="build",
                label="apps/web - build",
                module="apps/web",
                kind="build",
                argv=[sys.executable, "-c", "print('ok')"],
            ),
            CheckConfig(
                id="lint",
                label="apps/web - lint",
                module="apps/web",
                kind="lint",
                argv=[sys.executable, "-c", "print('ok')"],
            ),
            CheckConfig(
                id="typecheck",
                label="apps/web - typecheck",
                module="apps/web",
                kind="typecheck",
                argv=[sys.executable, "-c", "print('ok')"],
            ),
        ],
        notify=NotifyConfig(enabled=False),
    )

    report, _ = run_checks(
        config,
        config_path=Path(".agentshield/config.yaml"),
        used_config_file=True,
        strict=True,
        run_dir=tmp_path / ".qa-agent" / "runs",
    )

    missing_test = next(check for check in report.checks if check.kind == "test")
    missing_coverage = next(check for check in report.checks if check.kind == "coverage")
    assert "placeholder script" in missing_test.stderr_tail[-1]
    assert "does not include `vitest`" in missing_coverage.stderr_tail[-1]
