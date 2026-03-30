from __future__ import annotations

import builtins
from pathlib import Path

import agentshield_cli.cli as cli
from agentshield_cli.cli import main
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import ScanModuleSuggestion, ScanReport


def _full_module_checks(module: str) -> list[CheckConfig]:
    coverage_program = (
        "from pathlib import Path; "
        "Path('coverage.json').write_text('{\"totals\": {\"percent_covered\": 88.8}}', encoding='utf-8')"
    )
    return [
        CheckConfig(
            id=f"{module}-build",
            label=f"{module} - build",
            module=module,
            kind="build",
            argv=["python", "-c", "print('ok')"],
        ),
        CheckConfig(
            id=f"{module}-lint",
            label=f"{module} - lint",
            module=module,
            kind="lint",
            argv=["python", "-c", "print('ok')"],
        ),
        CheckConfig(
            id=f"{module}-typecheck",
            label=f"{module} - typecheck",
            module=module,
            kind="typecheck",
            argv=["python", "-c", "print('ok')"],
        ),
        CheckConfig(
            id=f"{module}-test",
            label=f"{module} - test",
            module=module,
            kind="test",
            argv=["python", "-c", "print('ok')"],
        ),
        CheckConfig(
            id=f"{module}-coverage",
            label=f"{module} - coverage",
            module=module,
            kind="coverage",
            argv=["python", "-c", coverage_program],
            coverage_parser="coverage.py-json",
            coverage_file="coverage.json",
        ),
    ]


def test_init_requires_yes_flag(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["init"])
    assert exit_code == 2


def test_check_auto_initializes_when_config_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".agentshield"
    written_config = config_dir / "config.yaml"

    def fake_initialize_project(*, bootstrap_config, config_path, used_config_file):
        del bootstrap_config, used_config_file
        checks = _full_module_checks("apps/api")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = AgentShieldConfig(project=ProjectConfig(name="demo", root="."), checks=checks)
        payload = {
            "version": 1,
            "project": {"name": "demo", "root": "."},
            "checks": [check.model_dump(mode="json", exclude_none=True) for check in checks],
        }
        import yaml

        config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return (
            config,
            ScanReport(project_name="demo", project_type="python", summary="demo"),
        )

    monkeypatch.setattr("agentshield_cli.cli.initialize_project", fake_initialize_project)
    exit_code = main(["check", "--strict"])

    assert exit_code == 0
    assert written_config.exists()


def test_check_no_init_fails_without_config(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["check", "--no-init"])
    assert exit_code == 2


def test_check_uses_interactive_init_when_tty(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    class _FakeStdin:
        def isatty(self) -> bool:
            return True

    def fake_interactive_initialize_project(*, bootstrap_config, config_path, used_config_file):
        del bootstrap_config, used_config_file
        checks = _full_module_checks("apps/api")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = AgentShieldConfig(project=ProjectConfig(name="demo", root="."), checks=checks)
        payload = {
            "version": 1,
            "project": {"name": "demo", "root": "."},
            "checks": [check.model_dump(mode="json", exclude_none=True) for check in checks],
        }
        import yaml

        config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return (
            config,
            ScanReport(project_name="demo", project_type="python", summary="demo"),
        )

    monkeypatch.setattr("agentshield_cli.cli._interactive_initialize_project", fake_interactive_initialize_project)
    monkeypatch.setattr("agentshield_cli.cli.sys.stdin", _FakeStdin())

    exit_code = main(["check", "--strict"])

    assert exit_code == 0
    assert (tmp_path / ".agentshield" / "config.yaml").exists()


def test_interactive_init_reviews_only_business_modules(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    prompts: list[str] = []
    answers = iter([""])

    report = ScanReport(
        project_name="demo",
        project_type="rust",
        summary="demo",
        modules=[
            ScanModuleSuggestion(
                name="merchant",
                path="src/merchant",
                language="Rust",
                confidence=0.95,
                recommended_checks=[],
            ),
            ScanModuleSuggestion(
                name="tests",
                path="tests",
                language="Rust",
                confidence=0.9,
                recommended_checks=[],
            ),
        ],
    )

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    def fake_build_checks(module, project_root):
        del project_root
        return [
            CheckConfig(
                id=f"{module.path}-test",
                label=f"{module.path} - test",
                module=module.path,
                kind="test",
                argv=["python", "-c", "print('ok')"],
            )
        ]

    monkeypatch.setattr(cli, "_run_scan_with_progress", lambda bootstrap_config: report)
    monkeypatch.setattr(cli, "build_checks_from_scan_module", fake_build_checks)
    monkeypatch.setattr(cli, "_configure_notify", lambda bootstrap_config: bootstrap_config.notify)
    monkeypatch.setattr(cli, "_edit_checks", lambda module, checks: checks)
    monkeypatch.setattr(builtins, "input", fake_input)

    generated_config, generated_report = cli._interactive_initialize_project(
        bootstrap_config=AgentShieldConfig(project=ProjectConfig(name="demo", root=".")),
        config_path=tmp_path / ".agentshield" / "config.yaml",
        used_config_file=False,
    )

    captured = capsys.readouterr().out
    assert generated_report.project_name == "demo"
    assert [check.module for check in generated_config.checks] == ["src/merchant"]
    assert "Sub-module 1/1: src/merchant" in captured
    assert "Sub-module 1/1: tests" not in captured
    assert "Detected: Rust · no framework detected" in captured
    assert prompts[0] == "Is the detection correct? [Y/n]: "


def test_interactive_init_can_skip_module(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    report = ScanReport(
        project_name="demo",
        project_type="rust",
        summary="demo",
        modules=[
            ScanModuleSuggestion(
                name="merchant",
                path="src/merchant",
                language="Rust",
                confidence=0.95,
                recommended_checks=[],
            ),
            ScanModuleSuggestion(
                name="payment_api",
                path="src/payment_api",
                language="Rust",
                confidence=0.95,
                recommended_checks=[],
            ),
        ],
    )

    def fake_build_checks(module, project_root):
        del project_root
        return [
            CheckConfig(
                id=f"{module.path}-test",
                label=f"{module.path} - test",
                module=module.path,
                kind="test",
                argv=["python", "-c", "print('ok')"],
            )
        ]

    edit_results = {
        "src/merchant": fake_build_checks(report.modules[0], tmp_path),
        "src/payment_api": [],
    }

    monkeypatch.setattr(cli, "_run_scan_with_progress", lambda bootstrap_config: report)
    monkeypatch.setattr(cli, "build_checks_from_scan_module", fake_build_checks)
    monkeypatch.setattr(cli, "_configure_notify", lambda bootstrap_config: bootstrap_config.notify)
    monkeypatch.setattr(
        cli,
        "_edit_checks",
        lambda module, checks: edit_results[module.path],
    )
    monkeypatch.setattr(cli, "_confirm", lambda prompt, default=False: True)

    generated_config, _ = cli._interactive_initialize_project(
        bootstrap_config=AgentShieldConfig(project=ProjectConfig(name="demo", root=".")),
        config_path=tmp_path / ".agentshield" / "config.yaml",
        used_config_file=False,
    )

    captured = capsys.readouterr().out
    assert [check.module for check in generated_config.checks] == ["src/merchant"]
    assert "Sub-module 1/2: src/merchant" in captured
    assert "Sub-module 2/2: src/payment_api" in captured
