from __future__ import annotations

from pathlib import Path

from agentshield_cli.bootstrap import build_config_from_scan
from agentshield_cli.config import AgentShieldConfig
from agentshield_cli.models import ScanCheckSuggestion, ScanModuleSuggestion, ScanReport


def test_build_config_from_scan_generates_argv_checks(tmp_path: Path) -> None:
    existing = AgentShieldConfig()
    report = ScanReport(
        project_name="demo-repo",
        project_type="python",
        summary="demo",
        modules=[
            ScanModuleSuggestion(
                name="api",
                path="apps/api",
                language="python",
                confidence=0.9,
                recommended_checks=[
                    ScanCheckSuggestion(id="test", argv=["pytest"]),
                    ScanCheckSuggestion(id="lint", run="ruff check .", cwd="apps/api"),
                ],
            )
        ],
    )

    config, payload = build_config_from_scan(
        report,
        project_root=tmp_path,
        existing_config=existing,
        include_llm=False,
        include_notify=False,
    )

    assert config.project.name == "demo-repo"
    assert config.checks[0].argv == ["pytest"]
    assert config.checks[1].cwd == "apps/api"
    assert "llm" not in payload


def test_build_config_from_scan_requires_checks(tmp_path: Path) -> None:
    existing = AgentShieldConfig()
    report = ScanReport(
        project_name="demo-repo",
        project_type="unknown",
        summary="demo",
        modules=[],
    )

    try:
        build_config_from_scan(
            report,
            project_root=tmp_path,
            existing_config=existing,
            include_llm=False,
            include_notify=False,
        )
    except ValueError as exc:
        assert "did not return any runnable checks" in str(exc)
    else:
        raise AssertionError("Expected analyzer config generation to fail without checks")
