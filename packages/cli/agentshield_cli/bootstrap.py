from __future__ import annotations

import shlex
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
CoverageParserKind = Literal["coverage.py-json", "istanbul-summary"]
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


def _infer_coverage_settings(
    suggestion: ScanCheckSuggestion,
    preset: CheckConfig | None,
) -> tuple[CoverageParserKind | None, str | None]:
    if preset is not None and preset.coverage_parser and preset.coverage_file:
        return preset.coverage_parser, preset.coverage_file

    argv = suggestion.resolved_argv()
    if argv is None and suggestion.run:
        argv = shlex.split(suggestion.run)
    if argv is None:
        return None, None

    for index, token in enumerate(argv):
        if token.startswith("--cov-report=json:"):
            return "coverage.py-json", token.split("json:", 1)[1]
        if token == "--cov-report" and index + 1 < len(argv):
            value = argv[index + 1]
            if value.startswith("json:"):
                return "coverage.py-json", value.split("json:", 1)[1]

    for index, token in enumerate(argv):
        reports_dir: str | None = None
        if token.startswith("--coverage.reportsDirectory="):
            reports_dir = token.split("=", 1)[1]
        elif token == "--coverage.reportsDirectory" and index + 1 < len(argv):
            reports_dir = argv[index + 1]
        if reports_dir:
            reports_dir = reports_dir.rstrip("/\\")
            return "istanbul-summary", f"{reports_dir}/coverage-summary.json"

    return None, None


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
) -> tuple[list[str] | None, str | None]:
    argv = suggestion.argv
    run = suggestion.run
    if module.language.lower() != "rust":
        return argv, run
    if argv is not None:
        return _normalize_rust_argv(argv), run
    if run is None:
        return None, None
    parsed = shlex.split(run)
    normalized = _normalize_rust_argv(parsed)
    if normalized != parsed:
        return normalized, None
    return None, run


def _build_check_from_suggestion(
    module: ScanModuleSuggestion,
    suggestion: ScanCheckSuggestion,
    preset_by_kind: dict[str, CheckConfig],
) -> CheckConfig | None:
    argv, run = _normalize_suggestion_command(module, suggestion)
    if argv is None and suggestion.run is None:
        return None

    module_path = module.path or module.name or "."
    inferred_kind = _normalize_kind(suggestion.id)
    preset = preset_by_kind.get(inferred_kind)
    coverage_parser = None
    coverage_file = None
    kind = inferred_kind
    if inferred_kind == "coverage":
        coverage_parser, coverage_file = _infer_coverage_settings(suggestion, preset)
        if coverage_parser is None or coverage_file is None:
            kind = "custom"

    identifier = kind if kind != "custom" else suggestion.id
    return CheckConfig(
        id=_check_id(module_path, identifier),
        label=f"{module_path} - {identifier}",
        module=module_path,
        kind=kind,
        argv=argv,
        run=run if argv is None else None,
        cwd=suggestion.cwd if suggestion.cwd is not None else (preset.cwd if preset is not None else None),
        coverage_parser=coverage_parser,
        coverage_file=coverage_file,
        timeout_sec=preset.timeout_sec if preset is not None else (1800 if kind in {"test", "coverage"} else 1200),
    )


def build_checks_from_scan_module(module: ScanModuleSuggestion, project_root: Path) -> list[CheckConfig]:
    preset_checks = build_preset_checks(module, project_root)
    preset_by_kind = {check.kind: check for check in preset_checks if check.kind in STANDARD_KINDS}

    ai_checks_by_kind: dict[str, CheckConfig] = {}
    custom_ai_checks: list[CheckConfig] = []
    for suggestion in module.recommended_checks:
        check = _build_check_from_suggestion(module, suggestion, preset_by_kind)
        if check is None:
            continue
        if check.kind in STANDARD_KINDS:
            ai_checks_by_kind[check.kind] = check
        else:
            custom_ai_checks.append(check)

    merged_checks: list[CheckConfig] = []
    for kind in STANDARD_KINDS:
        if kind in ai_checks_by_kind:
            merged_checks.append(ai_checks_by_kind[kind])
            continue
        preset = preset_by_kind.get(kind)
        if preset is not None:
            merged_checks.append(preset)

    if merged_checks or custom_ai_checks:
        return merged_checks + custom_ai_checks
    return preset_checks


def iter_checks_from_scan(report: ScanReport, project_root: Path) -> Iterable[CheckConfig]:
    for module in reviewable_modules(report.modules):
        for check in build_checks_from_scan_module(module, project_root):
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
