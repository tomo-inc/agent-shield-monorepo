from __future__ import annotations

from pathlib import Path

from agentshield_cli.baseline import apply_baseline_gates, build_baseline_record, write_baseline
from agentshield_cli.models import CheckResult, RunReport


def test_apply_baseline_gates_does_not_lower_default_coverage_gate(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".agentshield" / "baselines"
    baseline_report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file="baseline.json",
        checks=[
            CheckResult(
                id="apps-web-coverage",
                label="apps/web - coverage",
                module="apps/web",
                kind="coverage",
                command="pnpm exec vitest run --coverage",
                status="pass",
                exit_code=0,
                duration_sec=1.0,
                metrics={"line": 70.0},
            )
        ],
    )
    baseline_record = build_baseline_record(
        baseline_report,
        "apps/web",
        baseline_report.checks,
    )
    write_baseline(baseline_record, baseline_dir)

    current_report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        run_file="current.json",
        checks=[
            CheckResult(
                id="apps-web-coverage",
                label="apps/web - coverage",
                module="apps/web",
                kind="coverage",
                command="pnpm exec vitest run --coverage",
                status="fail",
                exit_code=0,
                duration_sec=1.0,
                metrics={"line": 65.0},
                gate_target=100.0,
                stderr_tail=["coverage line 65.0% below gate >= 100.0%"],
            )
        ],
    )

    updated = apply_baseline_gates(current_report, baseline_dir)

    assert updated.status == "fail"
    assert updated.checks[0].gate_target == 100.0
    assert updated.checks[0].stderr_tail[-1] == "coverage line 65.0% below gate >= 100.0%"
