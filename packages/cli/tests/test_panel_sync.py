from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib import error

from agentshield_cli.baseline import write_baseline
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import BaselineRecord, CheckResult, RunReport
from agentshield_cli.panel_sync import (
    build_baseline_upload_payload,
    build_project_register_payload,
    build_run_upload_payload,
    load_panel_settings,
    sync_baselines,
    sync_project_register,
    sync_run,
)


def _config(root: Path) -> AgentShieldConfig:
    return AgentShieldConfig(
        project=ProjectConfig(name="demo", root=str(root)),
        checks=[
            CheckConfig(id="build", label="apps/api - build", module="apps/api", kind="build", argv=["python", "-c", "print('ok')"]),
            CheckConfig(id="coverage", label="apps/api - coverage", module="apps/api", kind="coverage", argv=["python", "-c", "print('ok')"], coverage_parser="coverage.py-json", coverage_file="coverage.json"),
        ],
    )


def test_load_panel_settings_uses_env(monkeypatch) -> None:
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000/")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TOKEN", "secret")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TIMEOUT_SEC", "7")

    settings = load_panel_settings()

    assert settings is not None
    assert settings.base_url == "http://127.0.0.1:8000"
    assert settings.token == "secret"
    assert settings.timeout_sec == 7.0


def test_load_panel_settings_rejects_invalid_timeout(monkeypatch) -> None:
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TIMEOUT_SEC", "abc")

    try:
        load_panel_settings()
    except Exception as exc:  # noqa: BLE001
        assert str(exc) == "invalid AGENTSHIELD_PANEL_TIMEOUT_SEC: abc"
    else:
        raise AssertionError("expected timeout validation to fail")


def test_load_panel_settings_rejects_non_positive_timeout(monkeypatch) -> None:
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TIMEOUT_SEC", "0")

    try:
        load_panel_settings()
    except Exception as exc:  # noqa: BLE001
        assert str(exc) == "AGENTSHIELD_PANEL_TIMEOUT_SEC must be greater than 0"
    else:
        raise AssertionError("expected timeout validation to fail")


def test_build_project_register_payload_only_uses_accurate_fields(tmp_path: Path) -> None:
    payload = build_project_register_payload(_config(tmp_path), "ready")

    assert payload["project_key"] == "demo"
    assert payload["preset"] is None
    assert payload["commands"] is None
    assert payload["modules"] == [{"module_name": "apps/api", "stack": None, "language": None}]


def test_build_baseline_upload_payload_uses_line_threshold_only(tmp_path: Path) -> None:
    config = _config(tmp_path)
    baseline_dir = tmp_path / ".agentshield" / "baselines"
    write_baseline(
        BaselineRecord(
            module="apps/api",
            source_created_at="2026-03-30T00:00:00+00:00",
            source_run_file="run.json",
            thresholds={"line": 88.5, "branch": 70.0},
        ),
        baseline_dir,
    )

    payload = build_baseline_upload_payload(
        config,
        baseline_dir=baseline_dir,
        updated_at=datetime(2026, 3, 30, 0, 0, tzinfo=timezone.utc),
    )

    assert payload == {
        "project_key": "demo",
        "updated_at": "2026-03-30T00:00:00+00:00",
        "modules": [{"module_name": "apps/api", "baseline_pct": 88.5}],
    }


def test_build_baseline_upload_payload_returns_none_when_no_coverage_baseline(tmp_path: Path) -> None:
    config = _config(tmp_path)
    baseline_dir = tmp_path / ".agentshield" / "baselines"
    write_baseline(
        BaselineRecord(
            module="apps/api",
            source_created_at="2026-03-30T00:00:00+00:00",
            source_run_file="run.json",
            thresholds={"branch": 70.0},
        ),
        baseline_dir,
    )

    payload = build_baseline_upload_payload(
        config,
        baseline_dir=baseline_dir,
        updated_at=datetime(2026, 3, 30, 0, 0, tzinfo=timezone.utc),
    )

    assert payload is None


def test_build_run_upload_payload_omits_untrusted_fields(tmp_path: Path) -> None:
    config = _config(tmp_path)
    baseline_dir = tmp_path / ".agentshield" / "baselines"
    write_baseline(
        BaselineRecord(
            module="apps/api",
            source_created_at="2026-03-30T00:00:00+00:00",
            source_run_file="run.json",
            thresholds={"line": 88.0},
        ),
        baseline_dir,
    )
    report = RunReport(
        project_name="demo",
        status="fail",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=True,
        created_at="2026-03-30T00:00:00+00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[
            CheckResult(
                id="build",
                label="apps/api - build",
                module="apps/api",
                kind="build",
                command="python -c print('ok')",
                status="pass",
                exit_code=0,
                duration_sec=0.1,
            ),
            CheckResult(
                id="coverage",
                label="apps/api - coverage",
                module="apps/api",
                kind="coverage",
                command="python -c print('ok')",
                status="fail",
                exit_code=1,
                duration_sec=0.2,
                metrics={"line": 80.0},
                gate_target=88.0,
                stderr_tail=["coverage dropped"],
            ),
            CheckResult(
                id="custom",
                label="apps/api - custom",
                module="apps/api",
                kind="custom",
                command="custom",
                status="fail",
                exit_code=1,
                duration_sec=0.3,
                stderr_tail=["ignored"],
            ),
        ],
    )

    payload = build_run_upload_payload(config, report, baseline_dir=baseline_dir)

    assert payload["run_key"] == "2026-03-30T00-00-00+00-00.json"
    assert payload["source"] is None
    assert payload["started_at"] is None
    assert payload["duration_sec"] is None
    module_payload = payload["modules"][0]
    assert module_payload["status"] == "fail"
    assert module_payload["coverage_pct"] == 80.0
    assert module_payload["baseline_pct"] == 88.0
    assert module_payload["coverage_gate_pct"] == 88.0
    assert module_payload["coverage_delta_pct"] == -8.0
    assert len(module_payload["checker_results"]) == 2
    assert {item["checker"] for item in module_payload["checker_results"]} == {"build", "coverage"}


def test_sync_run_does_not_raise_on_http_error(monkeypatch, tmp_path: Path, capsys) -> None:
    config = _config(tmp_path)
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        created_at="2026-03-30T00:00:00+00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[],
    )
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")

    def fake_urlopen(req, timeout):  # noqa: ARG001
        raise error.HTTPError(
            req.full_url,
            404,
            "not found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("agentshield_cli.panel_sync.request.urlopen", fake_urlopen)

    assert sync_run(config, report, baseline_dir=tmp_path / ".agentshield" / "baselines") is False
    assert "Panel sync failed: run http 404" in capsys.readouterr().out


def test_sync_baselines_skips_when_no_baseline_data(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.delenv("AGENTSHIELD_PANEL_BASE_URL", raising=False)

    result = sync_baselines(
        _config(tmp_path),
        baseline_dir=tmp_path / ".agentshield" / "baselines",
        updated_at=datetime.now(timezone.utc),
    )

    assert result is False
    assert "Panel sync: baselines skipped (no coverage baseline data)" in capsys.readouterr().out


def test_sync_project_register_skips_when_panel_url_missing(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.delenv("AGENTSHIELD_PANEL_BASE_URL", raising=False)

    result = sync_project_register(_config(tmp_path), "ready")

    assert result is False
    assert "Panel sync: skipped" in capsys.readouterr().out


def test_sync_project_register_sets_bearer_token(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TOKEN", "secret")
    headers: dict[str, str] = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b"{}"

    def fake_urlopen(req, timeout):  # noqa: ARG001
        headers["Authorization"] = req.headers["Authorization"]
        return _Response()

    monkeypatch.setattr("agentshield_cli.panel_sync.request.urlopen", fake_urlopen)

    assert sync_project_register(_config(tmp_path), "ready") is True
    assert headers == {"Authorization": "Bearer secret"}
    assert "Panel sync: project register ok" in capsys.readouterr().out


def test_sync_run_handles_url_error(monkeypatch, tmp_path: Path, capsys) -> None:
    config = _config(tmp_path)
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        created_at="2026-03-30T00:00:00+00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[],
    )
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setattr(
        "agentshield_cli.panel_sync.request.urlopen",
        lambda req, timeout: (_ for _ in ()).throw(error.URLError("offline")),
    )

    assert sync_run(config, report, baseline_dir=tmp_path / ".agentshield" / "baselines") is False
    assert "Panel sync failed: run offline" in capsys.readouterr().out


def test_sync_run_handles_invalid_timeout_env(monkeypatch, tmp_path: Path, capsys) -> None:
    config = _config(tmp_path)
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        created_at="2026-03-30T00:00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[],
    )
    monkeypatch.setenv("AGENTSHIELD_PANEL_BASE_URL", "http://127.0.0.1:8000")
    monkeypatch.setenv("AGENTSHIELD_PANEL_TIMEOUT_SEC", "-1")

    assert sync_run(config, report, baseline_dir=tmp_path / ".agentshield" / "baselines") is False
    assert "Panel sync failed: AGENTSHIELD_PANEL_TIMEOUT_SEC must be greater than 0" in capsys.readouterr().out


def test_build_run_upload_payload_uses_label_when_module_missing(tmp_path: Path) -> None:
    config = _config(tmp_path)
    report = RunReport(
        project_name="demo",
        status="pass",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        created_at="2026-03-30T00:00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[
            CheckResult(
                id="build",
                label="apps/api - build",
                kind="build",
                command="python -c print('ok')",
                status="pass",
                exit_code=0,
                duration_sec=0.1,
                stdout_tail=["ok"],
            )
        ],
    )

    payload = build_run_upload_payload(config, report, baseline_dir=tmp_path / ".agentshield" / "baselines")

    module_payload = payload["modules"][0]
    assert module_payload["module_name"] == "apps/api"
    assert module_payload["status"] == "pass"
    assert module_payload["checker_results"][0]["detail"] == "ok"
    assert payload["finished_at"] == "2026-03-30T00:00:00+00:00"


def test_build_run_upload_payload_marks_timeout_module(tmp_path: Path) -> None:
    config = _config(tmp_path)
    report = RunReport(
        project_name="demo",
        status="timeout",
        config_path=".agentshield/config.yaml",
        used_config_file=True,
        strict=False,
        created_at="2026-03-30T00:00:00+00:00",
        run_file=str(tmp_path / ".qa-agent" / "runs" / "2026-03-30T00-00-00+00-00.json"),
        checks=[
            CheckResult(
                id="test",
                label="apps/api - test",
                module="apps/api",
                kind="test",
                command="pytest",
                status="timeout",
                exit_code=124,
                duration_sec=30.0,
            )
        ],
    )

    payload = build_run_upload_payload(config, report, baseline_dir=tmp_path / ".agentshield" / "baselines")

    assert payload["modules"][0]["status"] == "timeout"
