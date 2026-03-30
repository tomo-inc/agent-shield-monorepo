from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import yaml

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import ScanCheckSuggestion, ScanModuleSuggestion, ScanReport


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _timeout_for_check(check_id: str) -> int:
    lowered = check_id.lower()
    if "openapi" in lowered:
        return 600
    if "test" in lowered:
        return 1800
    return 1200


def _normalized_check(
    module: ScanModuleSuggestion,
    suggestion: ScanCheckSuggestion,
) -> CheckConfig | None:
    argv = suggestion.resolved_argv()
    if not argv:
        return None
    module_slug = _slug(module.path or module.name)
    check_slug = _slug(suggestion.id)
    check_id = f"{module_slug}-{check_slug}" if module_slug else check_slug
    return CheckConfig(
        id=check_id,
        label=f"{module.path} - {suggestion.id}",
        argv=argv,
        cwd=suggestion.cwd,
        timeout_sec=_timeout_for_check(suggestion.id),
    )


def _iter_checks(report: ScanReport) -> Iterable[CheckConfig]:
    for module in report.modules:
        for suggestion in module.recommended_checks:
            check = _normalized_check(module, suggestion)
            if check is not None:
                yield check


def build_config_from_scan(
    report: ScanReport,
    *,
    project_root: Path,
    existing_config: AgentShieldConfig,
    include_llm: bool,
    include_notify: bool,
) -> tuple[AgentShieldConfig, dict[str, object]]:
    checks = list(_iter_checks(report))
    if not checks:
        msg = "Analyzer did not return any runnable checks."
        raise ValueError(msg)

    config = AgentShieldConfig(
        version=1,
        project=ProjectConfig(name=report.project_name or project_root.name, root="."),
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
