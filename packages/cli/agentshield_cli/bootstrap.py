from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Literal

import yaml

from agentshield_cli.analyzer.ai_client import ScanAPIError, run_scan
from agentshield_cli.analyzer.scanner import collect_repo_snapshot
from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
from agentshield_cli.models import RepoSnapshot, ScanCheckSuggestion, ScanModuleSuggestion, ScanReport
from agentshield_cli.presets import build_preset_checks


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


STANDARD_KINDS = ("build", "lint", "typecheck", "test", "coverage")
CheckKind = Literal["build", "lint", "typecheck", "test", "coverage", "custom"]
TEST_ONLY_PATH_MARKERS = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "e2e",
}
RUST_SUBCOMMANDS = {
    "bench",
    "build",
    "check",
    "clippy",
    "doc",
    "fmt",
    "run",
    "test",
}


def _check_id(module_path: str, kind: str) -> str:
    return f"{_slug(module_path)}-{_slug(kind)}"


def _check_module_name(check: CheckConfig) -> str | None:
    if check.module:
        return check.module
    if " - " in check.label:
        return check.label.split(" - ", 1)[0]
    return None


def is_test_only_module(module: ScanModuleSuggestion) -> bool:
    parts = {part.lower() for part in Path(module.path).parts}
    if parts & TEST_ONLY_PATH_MARKERS:
        return True
    name_parts = {part.lower() for part in Path(module.name).parts}
    return bool(name_parts & TEST_ONLY_PATH_MARKERS)


def reviewable_modules(modules: list[ScanModuleSuggestion]) -> list[ScanModuleSuggestion]:
    return [module for module in modules if not is_test_only_module(module)]


def normalize_module_identity(
    module: ScanModuleSuggestion,
    snapshot: RepoSnapshot | None = None,
) -> ScanModuleSuggestion:
    path = Path(module.path)
    normalized_path = module.path
    normalized_name = module.name
    tree_entries = set(snapshot.tree) if snapshot is not None else set()

    if module.language.lower() == "rust":
        if path.suffix == ".rs" and path.parts[:2] == ("src", "bin"):
            module_dir = f"src/{path.stem}/"
            if module_dir in tree_entries:
                normalized_path = module_dir.removesuffix("/")
                normalized_name = path.stem
            else:
                normalized_path = path.stem
                normalized_name = path.stem
        elif path.name == "mod.rs":
            normalized_path = str(path.parent)
            normalized_name = path.parent.name or str(path.parent)
        elif path.suffix == ".rs":
            normalized_path = path.stem
            normalized_name = path.stem

    return module.model_copy(update={"path": normalized_path, "name": normalized_name})


def normalize_scan_report(report: ScanReport, snapshot: RepoSnapshot | None = None) -> ScanReport:
    normalized_modules = [normalize_module_identity(module, snapshot) for module in report.modules]
    return report.model_copy(update={"modules": normalized_modules})


def _normalize_kind(value: str) -> CheckKind:
    lowered = value.strip().lower()
    if not lowered:
        return "custom"
    if "coverage" in lowered or lowered == "cov":
        return "coverage"
    if any(token in lowered for token in ("typecheck", "type-check", "pyright", "mypy", "tsc")):
        return "typecheck"
    if any(token in lowered for token in ("lint", "ruff", "eslint", "clippy")):
        return "lint"
    if any(token in lowered for token in ("test", "pytest", "vitest", "jest")):
        return "test"
    if any(token in lowered for token in ("build", "compile")):
        return "build"
    return "custom"


def _normalize_rust_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0] == "cargo":
        return argv
    if argv[0] in RUST_SUBCOMMANDS:
        return ["cargo", *argv]
    return argv


def _normalize_suggestion_command(
    module: ScanModuleSuggestion,
    suggestion: ScanCheckSuggestion,
) -> list[str]:
    argv = suggestion.argv
    if module.language.lower() != "rust":
        return argv
    return _normalize_rust_argv(argv)


def _build_custom_check_from_suggestion(
    module: ScanModuleSuggestion,
    suggestion: ScanCheckSuggestion,
) -> CheckConfig | None:
    inferred_kind = _normalize_kind(suggestion.id)
    if inferred_kind in STANDARD_KINDS:
        return None

    module_path = module.path or module.name or "."
    argv = _normalize_suggestion_command(module, suggestion)
    return CheckConfig(
        id=_check_id(module_path, suggestion.id),
        label=f"{module_path} - {suggestion.id}",
        module=module_path,
        kind="custom",
        argv=argv,
        cwd=suggestion.cwd if suggestion.cwd is not None else module_path,
        timeout_sec=1200,
    )


def build_checks_from_scan_module(module: ScanModuleSuggestion, project_root: Path) -> list[CheckConfig]:
    preset_checks = build_preset_checks(module, project_root)
    custom_ai_checks: list[CheckConfig] = []
    for suggestion in module.recommended_checks:
        check = _build_custom_check_from_suggestion(module, suggestion)
        if check is None:
            continue
        custom_ai_checks.append(check)

    if preset_checks or custom_ai_checks:
        return preset_checks + custom_ai_checks
    return []


def iter_checks_from_scan(report: ScanReport, project_root: Path) -> Iterable[CheckConfig]:
    for module in reviewable_modules(report.modules):
        for check in build_checks_from_scan_module(module, project_root):
            yield check


def _validate_generated_checks(checks: list[CheckConfig]) -> None:
    issues: list[str] = []

    for check in checks:
        module_name = check.module or check.label.split(" - ", 1)[0]
        if check.run is not None:
            issues.append(
                f"Generated check `{check.id}` for module `{module_name}` still uses shell `run`; "
                "generated configs must use `argv` only."
            )

    if issues:
        raise ValueError("Generated config validation failed:\n- " + "\n- ".join(issues))


def _disabled_generated_standard_check(module_path: str, kind: CheckKind) -> CheckConfig:
    module_slug = _slug(module_path) or "root"
    payload: dict[str, object] = {
        "id": _check_id(module_path, f"{kind}-disabled"),
        "label": f"{module_path} - {kind}",
        "module": module_path,
        "kind": kind,
        "argv": ["true"],
        "cwd": module_path,
        "enabled": False,
    }
    if kind == "coverage":
        payload["coverage_parser"] = "istanbul-summary"
        payload["coverage_file"] = f".qa-agent/generated/coverage/{module_slug}/coverage-summary.json"
    return CheckConfig.model_validate(payload)


def _fill_missing_node_standard_checks(project_root: Path, checks: list[CheckConfig]) -> list[CheckConfig]:
    grouped: dict[str, list[CheckConfig]] = {}
    module_order: list[str] = []
    passthrough_checks: list[CheckConfig] = []
    for check in checks:
        module_name = _check_module_name(check)
        if module_name is None:
            passthrough_checks.append(check)
            continue
        if module_name not in grouped:
            grouped[module_name] = []
            module_order.append(module_name)
        grouped[module_name].append(check)

    augmented: list[CheckConfig] = []
    for module_name in module_order:
        module_checks = grouped[module_name]
        module_root = project_root / module_name
        standard_checks = [check for check in module_checks if check.kind in STANDARD_KINDS]
        custom_checks = [check for check in module_checks if check.kind not in STANDARD_KINDS]
        standard_by_kind = {check.kind: check for check in standard_checks}
        if not (module_root / "package.json").exists():
            augmented.extend(standard_by_kind[kind] for kind in STANDARD_KINDS if kind in standard_by_kind)
            augmented.extend(custom_checks)
            continue
        if not standard_checks:
            augmented.extend(standard_by_kind[kind] for kind in STANDARD_KINDS if kind in standard_by_kind)
            augmented.extend(custom_checks)
            continue
        for kind in STANDARD_KINDS:
            existing_check = standard_by_kind.get(kind)
            if existing_check is not None:
                augmented.append(existing_check)
            else:
                augmented.append(_disabled_generated_standard_check(module_name, kind))
        augmented.extend(custom_checks)
    augmented.extend(passthrough_checks)
    return augmented


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
    checks = _fill_missing_node_standard_checks(project_root, checks)
    _validate_generated_checks(checks)

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
    report = normalize_scan_report(run_scan(snapshot, bootstrap_config.llm), snapshot)
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


__all__ = [
    "ScanAPIError",
    "build_checks_from_scan_module",
    "initialize_project",
    "is_test_only_module",
    "normalize_scan_report",
    "reviewable_modules",
    "write_generated_config",
]
