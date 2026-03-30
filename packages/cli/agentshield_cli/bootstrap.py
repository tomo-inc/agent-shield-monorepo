from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import yaml

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import ScanReport
from agentshield_cli.presets import build_preset_checks


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def iter_checks_from_scan(report: ScanReport, project_root: Path) -> Iterable[CheckConfig]:
    for module in report.modules:
        for check in build_preset_checks(module, project_root):
            yield check


def build_config_payload(
    *,
    project_name: str,
    project_root: Path,
    checks: list[CheckConfig],
    existing_config: AgentShieldConfig,
    include_llm: bool,
    include_notify: bool,
) -> tuple[AgentShieldConfig, dict[str, object]]:
    if not checks:
        msg = "Analyzer did not return any runnable checks."
        raise ValueError(msg)

    config = AgentShieldConfig(
        version=1,
        project=ProjectConfig(name=project_name or project_root.name, root="."),
        checks=checks,
        llm=existing_config.llm,
        notify=existing_config.notify,
    )

    payload: dict[str, object] = {
        "version": config.version,
        "project": config.project.model_dump(mode="json", exclude_none=True),
        "checks": [check.model_dump(mode="json", exclude_none=True) for check in config.checks],
    }
    if include_llm:
        payload["llm"] = config.llm.model_dump(mode="json", exclude_none=True)
    if include_notify:
        payload["notify"] = config.notify.model_dump(mode="json", exclude_none=True)
    return config, payload


def build_config_from_scan(
    report: ScanReport,
    *,
    project_root: Path,
    existing_config: AgentShieldConfig,
    include_llm: bool,
    include_notify: bool,
) -> tuple[AgentShieldConfig, dict[str, object]]:
    checks = list(iter_checks_from_scan(report, project_root))
    return build_config_payload(
        project_name=report.project_name or project_root.name,
        project_root=project_root,
        checks=checks,
        existing_config=existing_config,
        include_llm=include_llm,
        include_notify=include_notify,
    )


def write_generated_config(payload: dict[str, object], config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def initialize_project(
    *,
    bootstrap_config: AgentShieldConfig,
    config_path: Path,
    used_config_file: bool,
) -> tuple[AgentShieldConfig, ScanReport]:
    snapshot = collect_repo_snapshot(bootstrap_config.project_root)
    report = run_scan(snapshot, bootstrap_config.llm)
    report.project_name = bootstrap_config.project.name
    generated_config, payload = build_config_from_scan(
        report,
        project_root=bootstrap_config.project_root,
        existing_config=bootstrap_config,
        include_llm=used_config_file,
        include_notify=used_config_file,
    )
    write_generated_config(payload, config_path)
    return generated_config, report


__all__ = ["ScanAPIError", "initialize_project", "write_generated_config"]
