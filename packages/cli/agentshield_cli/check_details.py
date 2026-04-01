from __future__ import annotations

import json
import re
from pathlib import Path

from agentshield_cli.models import CheckResult
from agentshield_cli.presets import explain_missing_standard_checks


_DETAILED_ERROR_MARKERS = (
    ": error:",
    "error:",
    "failed",
    "traceback",
    "exception",
    "unrecognized arguments",
    "command not found",
    "no module named",
    "did not generate",
    "missing",
)
_LOW_SIGNAL_PREFIXES = ("warning:", "note:", "info:")
_SUMMARY_ERROR_PATTERNS = (
    re.compile(r"^found \d+ error"),
    re.compile(r"^\d+ errors? generated"),
)
_NODE_MISSING_PACKAGE_PATTERNS = (
    re.compile(r"Cannot find package '([^']+)'"),
    re.compile(r"Cannot find dependency '([^']+)'"),
    re.compile(r"Cannot find module '([^']+)'"),
)
_NODE_PACKAGE_MANAGERS = ("pnpm", "npm", "yarn", "bun", "bunx")
_PACKAGE_MANAGER_LOCKFILES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pnpm", ("pnpm-lock.yaml", "pnpm-workspace.yaml")),
    ("yarn", ("yarn.lock",)),
    ("bun", ("bun.lock", "bun.lockb")),
    ("npm", ("package-lock.json", "npm-shrinkwrap.json")),
)
_VITEST_CONFIG_FILES = (
    "vitest.config.ts",
    "vitest.config.mts",
    "vitest.config.js",
    "vitest.config.mjs",
)
_VITEST_ENVIRONMENT_PACKAGES = {
    "happy-dom": "happy-dom",
    "jsdom": "jsdom",
}


def _load_json_file(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _normalize_package_manager(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.startswith("@") and normalized.count("@") >= 2:
        normalized = normalized.rsplit("@", 1)[0]
    else:
        normalized = normalized.split("@", 1)[0]
    if normalized == "@pnpm/exe":
        return "pnpm"
    return normalized or None


def _package_manager_from_lockfiles(root: Path) -> str | None:
    for package_manager, lockfiles in _PACKAGE_MANAGER_LOCKFILES:
        if any((root / lockfile).exists() for lockfile in lockfiles):
            return package_manager
    return None


def _detect_node_package_manager(
    project_root: Path,
    module_root: Path,
    module_package_data: dict[str, object] | None,
) -> str:
    if module_package_data is not None:
        package_manager = _normalize_package_manager(module_package_data.get("packageManager"))
        if package_manager:
            return package_manager
    module_lockfile_manager = _package_manager_from_lockfiles(module_root)
    if module_lockfile_manager:
        return module_lockfile_manager
    root_package_data = _load_json_file(project_root / "package.json")
    if root_package_data is not None:
        package_manager = _normalize_package_manager(root_package_data.get("packageManager"))
        if package_manager:
            return package_manager
    root_lockfile_manager = _package_manager_from_lockfiles(project_root)
    if root_lockfile_manager:
        return root_lockfile_manager
    return "npm"


def _dependency_names(package_data: dict[str, object] | None) -> set[str]:
    names: set[str] = set()
    if package_data is None:
        return names
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        raw = package_data.get(key)
        if not isinstance(raw, dict):
            continue
        names.update(str(name) for name in raw.keys())
    return names


def _module_name(check: CheckResult) -> str | None:
    if check.module:
        return check.module
    if " - " in check.label:
        return check.label.split(" - ", 1)[0]
    return None


def _command_prefix(command: str) -> str | None:
    tokens = command.split()
    if not tokens:
        return None
    return tokens[0]


def _iter_missing_node_packages(lines: list[str]) -> list[str]:
    packages: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for pattern in _NODE_MISSING_PACKAGE_PATTERNS:
            match = pattern.search(line)
            if match is None:
                continue
            package_name = match.group(1).strip()
            if not package_name or package_name.startswith((".", "/", "node:")):
                continue
            if package_name in seen:
                continue
            seen.add(package_name)
            packages.append(package_name)
    return packages


def _looks_installed(project_root: Path, module_root: Path, package_name: str) -> bool:
    package_parts = package_name.split("/")
    direct_locations = (
        module_root / "node_modules" / Path(*package_parts),
        project_root / "node_modules" / Path(*package_parts),
    )
    if any(location.exists() for location in direct_locations):
        return True

    pnpm_store = project_root / "node_modules" / ".pnpm"
    if not pnpm_store.exists():
        return False
    folder_prefix = package_name.replace("/", "+")
    return any(pnpm_store.glob(f"{folder_prefix}@*"))


def _recommended_install_command(package_manager: str, project_root: Path) -> str:
    if package_manager == "pnpm":
        if (project_root / "pnpm-lock.yaml").exists():
            return "pnpm install --frozen-lockfile"
        return "pnpm install"
    if package_manager == "yarn":
        if (project_root / "yarn.lock").exists():
            return "yarn install --immutable"
        return "yarn install"
    if package_manager == "bun":
        if (project_root / "bun.lock").exists() or (project_root / "bun.lockb").exists():
            return "bun install --frozen-lockfile"
        return "bun install"
    if (project_root / "package-lock.json").exists() or (project_root / "npm-shrinkwrap.json").exists():
        return "npm ci"
    return "npm install"


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _expected_vitest_environment_package(module_root: Path) -> str | None:
    for config_name in _VITEST_CONFIG_FILES:
        config_path = module_root / config_name
        if not config_path.exists():
            continue
        text = _read_text_file(config_path)
        if not text:
            continue
        match = re.search(r"environment\s*:\s*['\"]([^'\"]+)['\"]", text)
        if match is None:
            continue
        environment = match.group(1).strip()
        package_name = _VITEST_ENVIRONMENT_PACKAGES.get(environment)
        if package_name:
            return package_name
    return None


def _node_dependency_install_drift_reason(
    check: CheckResult,
    project_root: Path,
) -> str | None:
    module_name = _module_name(check)
    if not module_name:
        return None
    module_root = project_root / module_name
    if not (module_root / "package.json").exists():
        return None
    command_prefix = _command_prefix(check.command)
    if command_prefix not in _NODE_PACKAGE_MANAGERS:
        return None

    module_package_data = _load_json_file(module_root / "package.json")
    root_package_data = _load_json_file(project_root / "package.json")
    declared_paths: dict[str, str] = {}
    for package_name in _dependency_names(module_package_data):
        declared_paths[package_name] = f"{module_name}/package.json"
    for package_name in _dependency_names(root_package_data):
        declared_paths.setdefault(package_name, "package.json")

    if not declared_paths:
        return None

    candidates = _iter_missing_node_packages(check.stderr_tail + check.stdout_tail)
    for package_name in candidates:
        declared_in = declared_paths.get(package_name)
        if declared_in is None:
            continue
        if _looks_installed(project_root, module_root, package_name):
            continue
        package_manager = _detect_node_package_manager(project_root, module_root, module_package_data)
        install_command = _recommended_install_command(package_manager, project_root)
        return (
            f"`{package_name}` is declared in `{declared_in}` but is not installed in the current workspace. "
            f"Run `{install_command}` from the repo root to sync dependencies."
        )

    if check.kind in {"test", "coverage"} and "ERR_MODULE_NOT_FOUND" in " ".join(check.stderr_tail + check.stdout_tail):
        package_name = _expected_vitest_environment_package(module_root)
        if package_name:
            declared_in = declared_paths.get(package_name)
            if declared_in is not None and not _looks_installed(project_root, module_root, package_name):
                package_manager = _detect_node_package_manager(project_root, module_root, module_package_data)
                install_command = _recommended_install_command(package_manager, project_root)
                return (
                    f"`{package_name}` is declared in `{declared_in}` but is not installed in the current "
                    f"workspace. Run `{install_command}` from the repo root to sync dependencies."
                )
    return None


def _matches_summary_error(line: str) -> bool:
    lowered = line.lower()
    return any(pattern.match(lowered) for pattern in _SUMMARY_ERROR_PATTERNS)


def _select_from_lines(lines: list[str], *, skip_low_signal: bool) -> str | None:
    for line in reversed(lines):
        lowered = line.lower()
        if skip_low_signal and lowered.startswith(_LOW_SIGNAL_PREFIXES):
            continue
        if _matches_summary_error(lowered):
            continue
        if any(marker in lowered for marker in _DETAILED_ERROR_MARKERS):
            return line

    for line in reversed(lines):
        lowered = line.lower()
        if skip_low_signal and lowered.startswith(_LOW_SIGNAL_PREFIXES):
            continue
        if any(marker in lowered for marker in _DETAILED_ERROR_MARKERS) or _matches_summary_error(lowered):
            return line
    return None


def select_failure_reason(check: CheckResult, project_root: Path | None = None) -> str | None:
    if check.status == "pass":
        return None

    if project_root is not None:
        node_drift_reason = _node_dependency_install_drift_reason(check, project_root)
        if node_drift_reason:
            return node_drift_reason

    stderr_reason = _select_from_lines(check.stderr_tail, skip_low_signal=True)
    if stderr_reason:
        return stderr_reason

    stdout_reason = _select_from_lines(check.stdout_tail, skip_low_signal=False)
    if stdout_reason:
        return stdout_reason

    for line in reversed(check.stderr_tail):
        lowered = line.lower()
        if lowered.startswith(_LOW_SIGNAL_PREFIXES):
            continue
        return line

    if check.stdout_tail:
        return check.stdout_tail[-1]
    if check.stderr_tail:
        return check.stderr_tail[-1]
    return None


def missing_step_message(module_name: str, kind: str, project_root: Path) -> str:
    specific_reason = explain_missing_standard_checks(module_name, project_root).get(kind)
    if specific_reason:
        return specific_reason
    return (
        f"AgentShield did not generate a `{kind}` step for module `{module_name}` during setup. "
        "This module cannot pass until that step is added. Re-run `agentshield init --yes` to scan "
        "again, or add the command manually."
    )
