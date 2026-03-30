from __future__ import annotations

from pathlib import Path

from agentshield_cli.cli import main


def test_check_dry_run_skips_initial_baselines(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".agentshield"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "version: 1",
                "project:",
                "  name: demo",
                "  root: .",
                "checks:",
                "  - id: ok",
                "    label: apps/api - ok",
                "    argv:",
                "      - python",
                "      - -c",
                "      - print('ok')",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["check", "--strict", "--dry-run"])

    assert exit_code == 0
    assert (tmp_path / ".qa-agent" / "runs" / "latest.json").exists()
    assert not (tmp_path / ".agentshield" / "baselines").exists()

