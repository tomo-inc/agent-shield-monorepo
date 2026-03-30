from __future__ import annotations

from pathlib import Path

import yaml

from agentshield_cli.cli import main


def _full_check_yaml(module: str) -> str:
    coverage_program = (
        "from pathlib import Path; "
        "Path('coverage.json').write_text('{\"totals\": {\"percent_covered\": 88.8}}', encoding='utf-8')"
    )
    payload = {
        "version": 1,
        "project": {"name": "demo", "root": "."},
        "checks": [
            {
                "id": f"{module}-build",
                "label": f"{module} - build",
                "module": module,
                "kind": "build",
                "argv": ["python", "-c", "print('ok')"],
            },
            {
                "id": f"{module}-lint",
                "label": f"{module} - lint",
                "module": module,
                "kind": "lint",
                "argv": ["python", "-c", "print('ok')"],
            },
            {
                "id": f"{module}-typecheck",
                "label": f"{module} - typecheck",
                "module": module,
                "kind": "typecheck",
                "argv": ["python", "-c", "print('ok')"],
            },
            {
                "id": f"{module}-test",
                "label": f"{module} - test",
                "module": module,
                "kind": "test",
                "argv": ["python", "-c", "print('ok')"],
            },
            {
                "id": f"{module}-coverage",
                "label": f"{module} - coverage",
                "module": module,
                "kind": "coverage",
                "argv": ["python", "-c", coverage_program],
                "coverage_parser": "coverage.py-json",
                "coverage_file": "coverage.json",
            },
        ],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def test_check_dry_run_skips_initial_baselines(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".agentshield"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(_full_check_yaml("apps/api"), encoding="utf-8")

    exit_code = main(["check", "--strict", "--dry-run"])

    assert exit_code == 0
    assert (tmp_path / ".qa-agent" / "runs" / "latest.json").exists()
    assert not (tmp_path / ".agentshield" / "baselines").exists()


def test_check_prints_start_message_when_config_exists(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".agentshield"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(_full_check_yaml("apps/api"), encoding="utf-8")

    exit_code = main(["check", "--dry-run"])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "AgentShield Check" in captured
    assert "Config loaded: .agentshield/config.yaml" in captured
    assert "Running checks for 1 module(s)..." in captured
    assert "[apps/api] Build" in captured
