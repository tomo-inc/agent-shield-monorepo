from __future__ import annotations

import json
from pathlib import Path

from agentshield_cli.cli import main
from agentshield_cli.models import CheckResult, RunReport


def _write_report(run_dir: Path, name: str, status: str) -> None:
    report = RunReport(
        project_name="demo",
        status=status,
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        created_at=name.replace(".json", "").replace("+00-00", "+00:00"),
        run_file=str(run_dir / name),
        checks=[
            CheckResult(
                id="apps-api-test-api",
                label="apps/api - test:api",
                command="uv run --project apps/api pytest apps/api/tests",
                status=status,
                exit_code=0 if status == "pass" else 1,
                duration_sec=0.5,
            )
        ],
    )
    (run_dir / name).write_text(
        json.dumps(report.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def test_report_filters_by_module(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / ".qa-agent" / "runs"
    run_dir.mkdir(parents=True)
    _write_report(run_dir, "2026-03-30T00-00-00+00-00.json", "pass")
    _write_report(run_dir, "2026-03-29T00-00-00+00-00.json", "fail")

    exit_code = main(["report", "--last", "2", "--module", "apps/api"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Module filter: apps/api" in captured.out
    assert "apps-api-test-api: PASS" in captured.out
    assert "apps-api-test-api: FAIL" in captured.out

