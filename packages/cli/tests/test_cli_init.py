from __future__ import annotations

from pathlib import Path

from agentshield_cli.cli import main
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import ScanReport


def test_init_requires_yes_flag(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["init"])
    assert exit_code == 2


def test_check_auto_initializes_when_config_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".agentshield"
    written_config = config_dir / "config.yaml"

    def fake_initialize_project(*, bootstrap_config, config_path, used_config_file):
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "\n".join(
                [
                    "version: 1",
                    "project:",
                    "  name: demo",
                    "  root: .",
                    "checks:",
                    "  - id: ok",
                    "    label: OK",
                    "    argv:",
                    "      - python",
                    "      - -c",
                    "      - print('ok')",
                ]
            ),
            encoding="utf-8",
        )
        return (
            AgentShieldConfig(
                project=ProjectConfig(name="demo", root="."),
                checks=[CheckConfig(id="ok", label="OK", argv=["python", "-c", "print('ok')"])],
            ),
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
