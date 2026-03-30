from __future__ import annotations

import json
from pathlib import Path

from agentshield_cli.cli import main
from agentshield_cli.models import CheckResult, RunReport


def _write_run(run_dir: Path) -> RunReport:
    run_dir.mkdir(parents=True, exist_ok=True)
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file=str(run_dir / "2026-03-30T00-00-00+00-00.json"),
        checks=[
            CheckResult(
                id="apps-api-lint-api",
                label="apps/api - lint:api",
                command="uv run --project apps/api ruff check apps/api/app apps/api/tests",
                status="pass",
                exit_code=0,
                duration_sec=0.1,
            ),
            CheckResult(
                id="apps-web-test-web",
                label="apps/web - test:web",
                command="pnpm test:web",
                status="pass",
                exit_code=0,
                duration_sec=0.2,
            ),
        ],
    )
    payload = report.model_dump(mode="json")
    target = run_dir / "2026-03-30T00-00-00+00-00.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (run_dir / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report


def test_baseline_update_writes_module_baseline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _write_run(tmp_path / ".qa-agent" / "runs")
    monkeypatch.setattr("builtins.input", lambda _: "y")

    exit_code = main(["baseline", "update", "--module", "apps/api"])

    assert exit_code == 0
    assert (tmp_path / ".agentshield" / "baselines" / "apps-api.json").exists()

