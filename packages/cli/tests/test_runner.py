from __future__ import annotations

from pathlib import Path

from agentshield_cli.config import AgentShieldConfig, CheckConfig, NotifyConfig, ProjectConfig
from agentshield_cli.runner import run_checks


def test_run_checks_writes_report_and_marks_failure(tmp_path: Path) -> None:
    config = AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(tmp_path)),
        checks=[
            CheckConfig(id="ok", label="OK", run="python -c \"print('ok')\"", timeout_sec=5),
            CheckConfig(id="bad", label="Bad", run="python -c \"raise SystemExit(2)\"", timeout_sec=5),
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
        checks=[CheckConfig(id="ok", label="OK", run="python -c \"print('ok')\"", timeout_sec=5)],
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
