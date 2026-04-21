from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from agentshield_cli.config import CheckConfig
from agentshield_cli.models import ScanModuleSuggestion


PLACEHOLDER_TEST_MARKERS = (
    "no test",
    "no tests",
    "not implemented",
    "todo",
)
VITEST_COVERAGE_PACKAGES = {
    "@vitest/coverage-istanbul": "istanbul",
    "@vitest/coverage-v8": "v8",
}
C8_PACKAGE_SPEC = "c8@10.1.3"
PREFERRED_NODE_TEST_SCRIPTS = (
    "test:unit",
    "test-unit",
    "test:unit:ci",
    "test-unit-ci",
)
PYTHON_TOOL_GROUPS = {"dev", "lint", "qa", "test", "tests", "typecheck"}
NODE_SCRIPT_CHECKS: tuple[tuple[Literal["build", "lint", "typecheck"], str], ...] = (
    ("build", "build"),
    ("lint", "lint"),
    ("typecheck", "typecheck"),
)
PACKAGE_MANAGER_LOCKFILES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pnpm", ("pnpm-lock.yaml", "pnpm-workspace.yaml")),
    ("yarn", ("yarn.lock",)),
    ("bun", ("bun.lock", "bun.lockb")),
    ("npm", ("package-lock.json", "npm-shrinkwrap.json")),
)
ESLINT_CONFIG_FILES = (
    "eslint.config.js",
    "eslint.config.cjs",
    "eslint.config.mjs",
    "eslint.config.ts",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.mjs",
    ".eslintrc.json",
    ".eslintrc.yaml",
    ".eslintrc.yml",
)


@dataclass(frozen=True)
class NodeModuleFacts:
    package_manager: str
    scripts: dict[str, str]
    dependencies: set[str]
    dev_dependencies: set[str]


@dataclass(frozen=True)
class PythonModuleFacts:
    has_build_system: bool
    source_paths: list[str]
    test_paths: list[str]
    pyright_include: list[str]
    dependencies: set[str]
    optional_dependency_groups: dict[str, set[str]]

    @property
    def all_dependencies(self) -> set[str]:
        combined = set(self.dependencies)
        for names in self.optional_dependency_groups.values():
            combined.update(names)
        return combined


@dataclass(frozen=True)
class PythonModuleContext:
    facts: PythonModuleFacts
    manifest_root: str
    cwd: str
    inherited: bool
    source_target: str | None
    source_root: str | None
    test_targets: list[str]


@dataclass(frozen=True)
class GoModuleFacts:
    has_module_file: bool


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _module_key(module: ScanModuleSuggestion) -> str:
    language = module.language.lower()
    frameworks = {item.lower() for item in module.frameworks}
    if language in {"java", "kotlin"} or any("spring" in framework for framework in frameworks):
        return "java-maven"
    if language == "go":
        return "go"
    if language == "python":
        return "python"
    if language in {"typescript", "javascript"}:
        return "node"
    return "fallback"


def _check_id(module_path: str, kind: str) -> str:
    return f"{_slug(module_path)}-{_slug(kind)}"


def _load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _load_toml_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _dict_keys(value: object) -> set[str]:
    if not isinstance(value, dict):
        return set()
    return {str(key).lower() for key in value.keys()}


def _normalize_python_requirement(entry: object) -> str | None:
    if not isinstance(entry, str):
        return None
    match = re.match(r"[A-Za-z0-9_.-]+", entry.strip())
    if match is None:
        return None
    return match.group(0).lower()


def _parse_python_requirements(entries: object) -> set[str]:
    if not isinstance(entries, list):
        return set()
    names: set[str] = set()
    for entry in entries:
        normalized = _normalize_python_requirement(entry)
        if normalized:
            names.add(normalized)
    return names


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _existing_relative_dirs(module_root: Path, candidates: list[str]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        relative = Path(candidate)
        target = module_root / relative
        if not target.exists() or not target.is_dir():
            continue
        normalized = relative.as_posix()
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(normalized)
    return resolved


def _relative_generated_path(module_path: str, *parts: str) -> str:
    return _relative_generated_path_for_cwd(module_path, *parts)


def _relative_generated_path_for_cwd(cwd: str, *parts: str) -> str:
    root_prefix = Path(*([".."] * len(Path(cwd).parts)))
    return (root_prefix / ".qa-agent" / "generated" / Path(*parts)).as_posix()


def _path_depth(path: str) -> int:
    return len([part for part in Path(path).parts if part not in {"."}])


def _normalize_relative_path(path: Path) -> str:
    value = path.as_posix()
    return "." if value in {"", "."} else value


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
    except ValueError:
        return False
    return True


def _find_nearest_pyproject_root(project_root: Path, module_path: str) -> Path | None:
    current = (project_root / module_path).resolve()
    project_root = project_root.resolve()
    while _is_relative_to(current, project_root):
        if (current / "pyproject.toml").exists():
            return current
        if current == project_root:
            break
        current = current.parent
    return None


def _resolve_python_source_target(
    module_relative_path: str,
    source_paths: list[str],
) -> tuple[str | None, str | None]:
    module_path = Path(module_relative_path)
    parent_matches = [
        source_path
        for source_path in source_paths
        if _is_relative_to(module_path, Path(source_path))
    ]
    if parent_matches:
        source_root = max(parent_matches, key=_path_depth)
        return module_relative_path, source_root

    child_matches = [
        source_path
        for source_path in source_paths
        if _is_relative_to(Path(source_path), module_path)
    ]
    if child_matches:
        source_target = min(child_matches, key=_path_depth)
        return source_target, source_target

    return None, None


def _dedupe_paths(paths: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def _resolve_python_module_context(project_root: Path, module_path: str) -> PythonModuleContext | None:
    manifest_root = _find_nearest_pyproject_root(project_root, module_path)
    if manifest_root is None:
        return None

    manifest_root_relative = _normalize_relative_path(manifest_root.relative_to(project_root.resolve()))
    facts = _load_python_module_facts(project_root, manifest_root_relative)
    if facts is None:
        return None

    inherited = manifest_root_relative != module_path
    if not inherited:
        return PythonModuleContext(
            facts=facts,
            manifest_root=manifest_root_relative,
            cwd=module_path,
            inherited=False,
            source_target=None,
            source_root=None,
            test_targets=[],
        )

    module_root = (project_root / module_path).resolve()
    module_relative_path = _normalize_relative_path(module_root.relative_to(manifest_root))
    source_target, source_root = _resolve_python_source_target(module_relative_path, facts.source_paths)

    test_targets: list[str] = []
    if source_target is not None and source_root is not None:
        relative_inside_source = _normalize_relative_path(Path(source_target).relative_to(Path(source_root)))
        for test_root in facts.test_paths:
            candidate = Path(test_root)
            if relative_inside_source != ".":
                candidate = candidate / relative_inside_source
            if (manifest_root / candidate).exists():
                test_targets.append(candidate.as_posix())

    if source_target is None and not test_targets:
        return None

    return PythonModuleContext(
        facts=facts,
        manifest_root=manifest_root_relative,
        cwd=manifest_root_relative,
        inherited=True,
        source_target=source_target,
        source_root=source_root,
        test_targets=_dedupe_paths(test_targets),
    )


def _python_manifest_reference(context: PythonModuleContext, module_path: str) -> str:
    manifest_ref = "pyproject.toml" if context.manifest_root == "." else f"{context.manifest_root}/pyproject.toml"
    if not context.inherited:
        return f"`{manifest_ref}`"
    return f"`{manifest_ref}` inherited by `{module_path}`"


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


def _package_manager_from_manifest(package_data: dict[str, Any] | None) -> str | None:
    if not isinstance(package_data, dict):
        return None
    return _normalize_package_manager(package_data.get("packageManager"))


def _package_manager_from_lockfiles(root: Path) -> str | None:
    for package_manager, lockfiles in PACKAGE_MANAGER_LOCKFILES:
        if any((root / lockfile).exists() for lockfile in lockfiles):
            return package_manager
    return None


def _detect_package_manager(
    *,
    module_root: Path,
    project_root: Path,
    module_package_data: dict[str, Any] | None,
) -> str:
    module_package_manager = _package_manager_from_manifest(module_package_data)
    if module_package_manager:
        return module_package_manager

    module_lockfile_manager = _package_manager_from_lockfiles(module_root)
    if module_lockfile_manager:
        return module_lockfile_manager

    root_package_manager = _package_manager_from_manifest(_load_json_file(project_root / "package.json"))
    if root_package_manager:
        return root_package_manager

    root_lockfile_manager = _package_manager_from_lockfiles(project_root)
    if root_lockfile_manager:
        return root_lockfile_manager

    return "npm"


def _package_manager_run_argv(package_manager: str, script_name: str) -> list[str]:
    return [package_manager, "run", script_name]


def _package_manager_exec_argv(package_manager: str, command: list[str]) -> list[str]:
    if package_manager == "npm":
        return ["npm", "exec", "--", *command]
    if package_manager == "bun":
        return ["bunx", *command]
    return [package_manager, "exec", *command]


def _package_name_from_spec(package_spec: str) -> str:
    if package_spec.startswith("@") and package_spec.count("@") >= 2:
        return package_spec.rsplit("@", 1)[0]
    return package_spec.split("@", 1)[0]


def _package_manager_dlx_argv(package_manager: str, package_spec: str, args: list[str]) -> list[str]:
    if package_manager == "npm":
        return [
            "npm",
            "exec",
            "--yes",
            f"--package={package_spec}",
            "--",
            _package_name_from_spec(package_spec),
            *args,
        ]
    if package_manager == "bun":
        return ["bunx", package_spec, *args]
    if package_manager == "yarn":
        return ["yarn", "dlx", package_spec, *args]
    return [package_manager, "dlx", package_spec, *args]


def _is_placeholder_test_script(script: str) -> bool:
    lowered = script.lower()
    if any(marker in lowered for marker in PLACEHOLDER_TEST_MARKERS):
        return True
    return re.search(r"\bno\b.*\btests?\b", lowered) is not None


def _select_node_test_script(scripts: dict[str, str]) -> str | None:
    exact_test = scripts.get("test")
    if exact_test and not _is_placeholder_test_script(exact_test):
        return "test"

    for script_name in PREFERRED_NODE_TEST_SCRIPTS:
        script = scripts.get(script_name)
        if script and not _is_placeholder_test_script(script):
            return script_name

    candidates = [
        script_name
        for script_name, script in scripts.items()
        if script_name != "test"
        and (script_name.startswith("test:") or script_name.startswith("test-"))
        and not _is_placeholder_test_script(script)
    ]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _is_node_builtin_test_command(script: str) -> bool:
    tokens = re.findall(r"\S+", script.lower())
    saw_node = False
    for token in tokens:
        binary_name = token.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if binary_name in {"node", "node.exe"}:
            saw_node = True
            continue
        if saw_node and token == "--test":
            return True
    return False


def _can_infer_node_typecheck(module_root: Path, facts: NodeModuleFacts) -> bool:
    dependency_names = facts.dependencies | facts.dev_dependencies
    return "typescript" in dependency_names and (module_root / "tsconfig.json").exists()


def _infer_node_lint_argv(
    module_root: Path,
    package_data: dict[str, Any] | None,
    facts: NodeModuleFacts,
) -> list[str] | None:
    if not _has_eslint_config(module_root, package_data):
        return None
    dependency_names = facts.dependencies | facts.dev_dependencies
    if "next" in dependency_names and "eslint" in dependency_names:
        return _package_manager_exec_argv(facts.package_manager, ["next", "lint"])
    if "eslint" in dependency_names:
        return _package_manager_exec_argv(facts.package_manager, ["eslint", "."])
    return None


def _load_node_module_facts(project_root: Path, module_path: str) -> NodeModuleFacts | None:
    module_root = project_root / module_path
    package_data = _load_json_file(module_root / "package.json")
    if package_data is None:
        return None
    scripts = package_data.get("scripts")
    if not isinstance(scripts, dict):
        scripts = {}
    return NodeModuleFacts(
        package_manager=_detect_package_manager(
            module_root=module_root,
            project_root=project_root,
            module_package_data=package_data,
        ),
        scripts={str(key): str(value) for key, value in scripts.items() if isinstance(value, str)},
        dependencies=_dict_keys(package_data.get("dependencies")),
        dev_dependencies=_dict_keys(package_data.get("devDependencies")),
    )


def _has_eslint_config(module_root: Path, package_data: dict[str, Any] | None) -> bool:
    if package_data is not None and isinstance(package_data.get("eslintConfig"), dict):
        return True
    return any((module_root / config_name).exists() for config_name in ESLINT_CONFIG_FILES)


def _should_skip_interactive_next_lint(
    module_root: Path,
    package_data: dict[str, Any] | None,
    script_name: str,
    script_command: str,
) -> bool:
    if script_name != "lint":
        return False
    normalized = script_command.strip().lower()
    if normalized != "next lint":
        return False
    return not _has_eslint_config(module_root, package_data)


def _load_python_module_facts(project_root: Path, module_path: str) -> PythonModuleFacts | None:
    pyproject = _load_toml_file(project_root / module_path / "pyproject.toml")
    if pyproject is None:
        return None

    module_root = project_root / module_path
    project = pyproject.get("project", {})
    tool = pyproject.get("tool", {})
    hatch_wheel = (
        tool.get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
    )
    setuptools_find = (
        tool.get("setuptools", {})
        .get("packages", {})
        .get("find", {})
    )
    pytest_options = tool.get("pytest", {}).get("ini_options", {})
    pyright_options = tool.get("pyright", {})

    source_candidates = _as_string_list(hatch_wheel.get("packages"))
    source_candidates.extend(_as_string_list(setuptools_find.get("where")))
    for conventional_dir in ("src", "app"):
        if (module_root / conventional_dir).is_dir():
            source_candidates.append(conventional_dir)
    if not source_candidates:
        for child in sorted(module_root.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                source_candidates.append(child.name)
    source_paths = _existing_relative_dirs(module_root, source_candidates)

    test_candidates = _as_string_list(pytest_options.get("testpaths"))
    if not test_candidates and (module_root / "tests").is_dir():
        test_candidates.append("tests")
    test_paths = _existing_relative_dirs(module_root, test_candidates)
    pyright_include = _existing_relative_dirs(module_root, _as_string_list(pyright_options.get("include")))

    optional_dependency_groups: dict[str, set[str]] = {}
    optional_dependencies = project.get("optional-dependencies", {})
    if isinstance(optional_dependencies, dict):
        for group_name, requirements in optional_dependencies.items():
            if not isinstance(group_name, str):
                continue
            normalized_group = group_name.lower()
            optional_dependency_groups[normalized_group] = _parse_python_requirements(requirements)

    return PythonModuleFacts(
        has_build_system=isinstance(pyproject.get("build-system"), dict),
        source_paths=source_paths,
        test_paths=test_paths,
        pyright_include=pyright_include,
        dependencies=_parse_python_requirements(project.get("dependencies")),
        optional_dependency_groups=optional_dependency_groups,
    )


def _load_go_module_facts(project_root: Path, module_path: str) -> GoModuleFacts | None:
    if not (project_root / module_path / "go.mod").exists():
        return None
    return GoModuleFacts(has_module_file=True)


def _python_uv_run_prefix(
    facts: PythonModuleFacts,
    required_tools: set[str],
    *,
    with_tools: list[str] | None = None,
) -> list[str]:
    prefix = ["uv", "run"]
    extras = sorted(
        group_name
        for group_name, dependencies in facts.optional_dependency_groups.items()
        if group_name in PYTHON_TOOL_GROUPS and required_tools & dependencies
    )
    for extra in extras:
        prefix.extend(["--extra", extra])
    for tool in with_tools or []:
        prefix.extend(["--with", tool])
    return prefix


def _default_python_type_targets(context: PythonModuleContext) -> list[str]:
    facts = context.facts
    if not context.inherited:
        return facts.pyright_include or facts.source_paths or ["."]
    if context.source_target is not None:
        return [context.source_target]
    return facts.pyright_include or facts.source_paths or ["."]


def _build_node_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    facts = _load_node_module_facts(project_root, module_path)
    if facts is None:
        return []
    module_root = project_root / module_path
    package_data = _load_json_file(module_root / "package.json")
    module_slug = _slug(module_path) or "root"

    checks: list[CheckConfig] = []
    for kind, script_name in NODE_SCRIPT_CHECKS:
        if script_name not in facts.scripts:
            continue
        if _should_skip_interactive_next_lint(
            module_root,
            package_data,
            script_name,
            facts.scripts[script_name],
        ):
            continue
        checks.append(
            CheckConfig(
                id=_check_id(module_path, kind),
                label=f"{module_path} - {kind}",
                module=module_path,
                kind=kind,
                argv=_package_manager_run_argv(facts.package_manager, script_name),
                cwd=module_path,
            )
        )

    if not any(check.kind == "lint" for check in checks):
        inferred_lint_argv = _infer_node_lint_argv(module_root, package_data, facts)
        if inferred_lint_argv is not None:
            checks.append(
                CheckConfig(
                    id=_check_id(module_path, "lint"),
                    label=f"{module_path} - lint",
                    module=module_path,
                    kind="lint",
                    argv=inferred_lint_argv,
                    cwd=module_path,
                )
            )

    if "typecheck" not in facts.scripts and _can_infer_node_typecheck(module_root, facts):
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=_package_manager_exec_argv(facts.package_manager, ["tsc", "--noEmit"]),
                cwd=module_path,
            )
        )

    test_script_name = _select_node_test_script(facts.scripts)
    test_script = facts.scripts.get(test_script_name) if test_script_name is not None else None
    if test_script_name is not None:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "test"),
                label=f"{module_path} - test",
                module=module_path,
                kind="test",
                argv=_package_manager_run_argv(facts.package_manager, test_script_name),
                cwd=module_path,
                timeout_sec=1800,
            )
        )

    dependency_names = facts.dependencies | facts.dev_dependencies
    coverage_provider = None
    for package_name, provider in VITEST_COVERAGE_PACKAGES.items():
        if package_name in dependency_names:
            coverage_provider = provider
            break
    if "vitest" in dependency_names and coverage_provider is not None:
        coverage_dir = _relative_generated_path(module_path, "coverage", module_slug)
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "coverage"),
                label=f"{module_path} - coverage",
                module=module_path,
                kind="coverage",
                argv=_package_manager_exec_argv(
                    facts.package_manager,
                    [
                        "vitest",
                        "run",
                        "--coverage.enabled=true",
                        f"--coverage.provider={coverage_provider}",
                        "--coverage.reporter=json-summary",
                        "--coverage.reporter=text",
                        f"--coverage.reportsDirectory={coverage_dir}",
                    ],
                ),
                cwd=module_path,
                coverage_parser="istanbul-summary",
                coverage_file=f"{coverage_dir}/coverage-summary.json",
                timeout_sec=1800,
            )
        )
    elif test_script_name is not None and test_script is not None and _is_node_builtin_test_command(test_script):
        coverage_dir = _relative_generated_path(module_path, "coverage", module_slug)
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "coverage"),
                label=f"{module_path} - coverage",
                module=module_path,
                kind="coverage",
                argv=_package_manager_dlx_argv(
                    facts.package_manager,
                    C8_PACKAGE_SPEC,
                    [
                        "--reporter=json-summary",
                        "--reporter=text",
                        "--reports-dir",
                        coverage_dir,
                        *_package_manager_run_argv(facts.package_manager, test_script_name),
                    ],
                ),
                cwd=module_path,
                coverage_parser="istanbul-summary",
                coverage_file=f"{coverage_dir}/coverage-summary.json",
                timeout_sec=1800,
            )
        )

    return checks


def _build_python_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    context = _resolve_python_module_context(project_root, module_path)
    if context is None:
        return []
    facts = context.facts
    has_inherited_targets = context.inherited and bool(context.source_target is not None or context.test_targets)

    checks: list[CheckConfig] = []
    cwd = context.cwd
    if context.inherited:
        lint_targets = _dedupe_paths(
            ([context.source_target] if context.source_target is not None else []) + context.test_targets
        )
        if not lint_targets and context.source_target is not None:
            lint_targets = [context.source_target]
    else:
        lint_targets = facts.source_paths + facts.test_paths
        if not lint_targets:
            lint_targets = ["."]

    if facts.has_build_system:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "build"),
                label=f"{module_path} - build",
                module=module_path,
                kind="build",
                argv=["uv", "build", "."],
                cwd=cwd,
            )
        )

    if "ruff" in facts.all_dependencies:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "lint"),
                label=f"{module_path} - lint",
                module=module_path,
                kind="lint",
                argv=[*_python_uv_run_prefix(facts, {"ruff"}), "ruff", "check", *lint_targets],
                cwd=cwd,
            )
        )
    elif "black" in facts.all_dependencies:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "lint"),
                label=f"{module_path} - lint",
                module=module_path,
                kind="lint",
                argv=[*_python_uv_run_prefix(facts, {"black"}), "black", "--check", *lint_targets],
                cwd=cwd,
            )
        )
    elif has_inherited_targets:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "lint"),
                label=f"{module_path} - lint",
                module=module_path,
                kind="lint",
                argv=[*_python_uv_run_prefix(facts, set(), with_tools=["ruff"]), "ruff", "check", *lint_targets],
                cwd=cwd,
            )
        )

    if "pyright" in facts.all_dependencies:
        type_targets = _default_python_type_targets(context)
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=[*_python_uv_run_prefix(facts, {"pyright"}), "pyright", *type_targets],
                cwd=cwd,
            )
        )
    elif "mypy" in facts.all_dependencies:
        if context.inherited and context.source_target is not None:
            type_targets = [context.source_target]
        else:
            type_targets = facts.source_paths or ["."]
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=[*_python_uv_run_prefix(facts, {"mypy"}), "mypy", *type_targets],
                cwd=cwd,
            )
        )
    elif has_inherited_targets:
        type_targets = _default_python_type_targets(context)
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=[*_python_uv_run_prefix(facts, set(), with_tools=["pyright"]), "pyright", *type_targets],
                cwd=cwd,
            )
        )

    if context.inherited:
        pytest_args = context.test_targets or ([context.source_target] if context.source_target is not None else [])
    else:
        pytest_args = facts.test_paths or ["tests"]
    if "pytest" in facts.all_dependencies:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "test"),
                label=f"{module_path} - test",
                module=module_path,
                kind="test",
                argv=[*_python_uv_run_prefix(facts, {"pytest"}), "pytest", *pytest_args],
                cwd=cwd,
                timeout_sec=1800,
            )
        )

    coverage_target = context.source_target if context.inherited else (facts.source_paths[0] if facts.source_paths else None)
    coverage_prefix: list[str] | None = None
    if "pytest" in facts.all_dependencies and "pytest-cov" in facts.all_dependencies and coverage_target is not None:
        coverage_prefix = _python_uv_run_prefix(facts, {"pytest", "pytest-cov"})
    elif "pytest" in facts.all_dependencies and context.inherited and coverage_target is not None:
        coverage_prefix = _python_uv_run_prefix(facts, {"pytest"}, with_tools=["pytest-cov"])
    if coverage_prefix is not None:
        coverage_file = _relative_generated_path_for_cwd(cwd, "coverage", _slug(module_path), "coverage.json")
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "coverage"),
                label=f"{module_path} - coverage",
                module=module_path,
                kind="coverage",
                argv=[
                    *coverage_prefix,
                    "pytest",
                    f"--cov={coverage_target}",
                    f"--cov-report=json:{coverage_file}",
                    *pytest_args,
                ],
                cwd=cwd,
                coverage_parser="coverage.py-json",
                coverage_file=coverage_file,
                timeout_sec=1800,
            )
        )

    return checks


def _build_go_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    facts = _load_go_module_facts(project_root, module_path)
    if facts is None or not facts.has_module_file:
        return []

    coverage_file = _relative_generated_path(module_path, "coverage", _slug(module_path), "coverage.out")
    return [
        CheckConfig(
            id=_check_id(module_path, "build"),
            label=f"{module_path} - build",
            module=module_path,
            kind="build",
            argv=["go", "build", "./..."],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "lint"),
            label=f"{module_path} - lint",
            module=module_path,
            kind="lint",
            argv=["go", "vet", "./..."],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "typecheck"),
            label=f"{module_path} - typecheck",
            module=module_path,
            kind="typecheck",
            argv=["go", "test", "-run", "^$", "./..."],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "test"),
            label=f"{module_path} - test",
            module=module_path,
            kind="test",
            argv=["go", "test", "./..."],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "coverage"),
            label=f"{module_path} - coverage",
            module=module_path,
            kind="coverage",
            argv=["go", "test", f"-coverprofile={coverage_file}", "-covermode=count", "./..."],
            cwd=module_path,
            coverage_parser="go-coverprofile",
            coverage_file=coverage_file,
            timeout_sec=1800,
        ),
    ]


def _read_pom(project_root: Path, module_path: str) -> str:
    pom_path = project_root / module_path / "pom.xml"
    if not pom_path.exists():
        return ""
    return pom_path.read_text(encoding="utf-8")


def _build_java_maven_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    pom_text = _read_pom(project_root, module_path)
    has_spotless = "spotless-maven-plugin" in pom_text
    has_checkstyle = "maven-checkstyle-plugin" in pom_text
    has_jacoco = "jacoco-maven-plugin" in pom_text

    checks = [
        CheckConfig(
            id=_check_id(module_path, "build"),
            label=f"{module_path} - build",
            module=module_path,
            kind="build",
            argv=["mvn", "-B", "-DskipTests", "package"],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "typecheck"),
            label=f"{module_path} - typecheck",
            module=module_path,
            kind="typecheck",
            argv=["mvn", "-B", "-DskipTests", "compile"],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "test"),
            label=f"{module_path} - test",
            module=module_path,
            kind="test",
            argv=["mvn", "-B", "test"],
            cwd=module_path,
            timeout_sec=1800,
        ),
    ]

    if has_spotless:
        checks.insert(
            1,
            CheckConfig(
                id=_check_id(module_path, "lint"),
                label=f"{module_path} - lint",
                module=module_path,
                kind="lint",
                argv=["mvn", "-B", "spotless:check"],
                cwd=module_path,
                timeout_sec=1800,
            ),
        )
    elif has_checkstyle:
        checks.insert(
            1,
            CheckConfig(
                id=_check_id(module_path, "lint"),
                label=f"{module_path} - lint",
                module=module_path,
                kind="lint",
                argv=["mvn", "-B", "checkstyle:check"],
                cwd=module_path,
                timeout_sec=1800,
            ),
        )

    if has_jacoco:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "coverage"),
                label=f"{module_path} - coverage",
                module=module_path,
                kind="coverage",
                argv=["mvn", "-B", "test", "jacoco:report"],
                cwd=module_path,
                coverage_parser="jacoco-xml",
                coverage_file=".",
                timeout_sec=1800,
            )
        )

    return checks


def _explain_missing_node_checks(module_path: str, project_root: Path) -> dict[str, str]:
    facts = _load_node_module_facts(project_root, module_path)
    if facts is None:
        return {}
    module_root = project_root / module_path
    package_data = _load_json_file(module_root / "package.json")

    reasons: dict[str, str] = {}
    lint_script = facts.scripts.get("lint")
    if lint_script and _should_skip_interactive_next_lint(module_root, package_data, "lint", lint_script):
        reasons["lint"] = (
            f"`{module_path}/package.json` uses `next lint` but no ESLint config was found in `{module_path}`. "
            "AgentShield skipped the lint step to avoid Next.js interactive setup."
        )
    elif lint_script is None and _infer_node_lint_argv(module_root, package_data, facts) is None:
        if _has_eslint_config(module_root, package_data):
            reasons["lint"] = (
                f"`{module_path}/package.json` does not define a `lint` script and its dependencies do not "
                "expose an inferable ESLint runner, so AgentShield could not generate a lint step."
            )
        else:
            reasons["lint"] = (
                f"`{module_path}/package.json` does not define a `lint` script and no ESLint config was found "
                f"in `{module_path}`, so AgentShield could not generate a lint step."
            )
    if "typecheck" not in facts.scripts and not _can_infer_node_typecheck(module_root, facts):
        if "typescript" not in (facts.dependencies | facts.dev_dependencies):
            reasons["typecheck"] = (
                f"`{module_path}/package.json` does not define a `typecheck` script and does not include "
                "`typescript`, so AgentShield could not generate a typecheck step."
            )
        elif not (module_root / "tsconfig.json").exists():
            reasons["typecheck"] = (
                f"`{module_path}` does not define a `typecheck` script and no `tsconfig.json` was found, "
                "so AgentShield could not generate a typecheck step."
            )
    test_script = facts.scripts.get("test")
    if test_script is None:
        inferred_test_script = _select_node_test_script(facts.scripts)
        if inferred_test_script is None:
            reasons["test"] = (
                f"`{module_path}/package.json` does not define a `test` script, so AgentShield could not "
                "generate a test step."
            )
    elif _is_placeholder_test_script(test_script):
        reasons["test"] = (
            f"`{module_path}/package.json` defines `test` as a placeholder script (`{test_script}`), "
            "so AgentShield treated it as missing real test coverage."
        )

    dependency_names = facts.dependencies | facts.dev_dependencies
    inferred_test_script = _select_node_test_script(facts.scripts)
    inferred_test_command = facts.scripts.get(inferred_test_script) if inferred_test_script is not None else None
    has_node_builtin_coverage = (
        inferred_test_command is not None and _is_node_builtin_test_command(inferred_test_command)
    )
    if "vitest" not in dependency_names and not has_node_builtin_coverage:
        reasons["coverage"] = (
            f"`{module_path}/package.json` does not include `vitest`, and AgentShield could not infer a "
            "`node --test` unit-test script for the module, so it could not generate a JS coverage step."
        )
    elif (
        "vitest" in dependency_names
        and not any(package_name in dependency_names for package_name in VITEST_COVERAGE_PACKAGES)
        and not has_node_builtin_coverage
    ):
        reasons["coverage"] = (
            f"`{module_path}/package.json` does not include `@vitest/coverage-v8` or "
            "`@vitest/coverage-istanbul`, so AgentShield could not generate a coverage step."
        )

    return reasons


def _explain_missing_python_checks(module_path: str, project_root: Path) -> dict[str, str]:
    context = _resolve_python_module_context(project_root, module_path)
    if context is None:
        return {}
    facts = context.facts
    manifest_reference = _python_manifest_reference(context, module_path)
    has_inherited_targets = context.inherited and bool(context.source_target is not None or context.test_targets)
    has_inherited_coverage = context.inherited and context.source_target is not None and "pytest" in facts.all_dependencies

    reasons: dict[str, str] = {}
    if not facts.has_build_system:
        reasons["build"] = (
            f"{manifest_reference} does not define a build system, so AgentShield could not "
            "generate a build step."
        )
    if "ruff" not in facts.all_dependencies and "black" not in facts.all_dependencies and not has_inherited_targets:
        reasons["lint"] = (
            f"{manifest_reference} does not include `ruff` or `black` in dependencies or optional "
            "dependency groups, so AgentShield could not generate a lint step."
        )
    if "pyright" not in facts.all_dependencies and "mypy" not in facts.all_dependencies and not has_inherited_targets:
        reasons["typecheck"] = (
            f"{manifest_reference} does not include `pyright` or `mypy`, so AgentShield could not "
            "generate a typecheck step."
        )
    if "pytest" not in facts.all_dependencies:
        reasons["test"] = (
            f"{manifest_reference} does not include `pytest`, so AgentShield could not generate "
            "a test step."
        )
    if "pytest" not in facts.all_dependencies:
        reasons["coverage"] = (
            f"{manifest_reference} does not include `pytest`, so AgentShield could not generate "
            "a coverage step."
        )
    elif "pytest-cov" not in facts.all_dependencies and not has_inherited_coverage:
        reasons["coverage"] = (
            f"{manifest_reference} does not include `pytest-cov`, so AgentShield could not "
            "generate a coverage step."
        )
    elif context.inherited and context.source_target is None:
        reasons["coverage"] = (
            f"{manifest_reference} does not cover `{module_path}` as a detectable Python source target, "
            "so AgentShield could not infer a coverage target."
        )
    elif not facts.source_paths:
        reasons["coverage"] = (
            f"{manifest_reference} does not expose a detectable source package path, so AgentShield "
            "could not infer a coverage target."
        )

    return reasons


def _explain_missing_java_checks(module_path: str, project_root: Path) -> dict[str, str]:
    pom_text = _read_pom(project_root, module_path)
    if not pom_text:
        return {}

    reasons: dict[str, str] = {}
    if "spotless-maven-plugin" not in pom_text and "maven-checkstyle-plugin" not in pom_text:
        reasons["lint"] = (
            f"`{module_path}/pom.xml` does not configure Spotless or Checkstyle, so AgentShield could not "
            "generate a lint step."
        )
    if "jacoco-maven-plugin" not in pom_text:
        reasons["coverage"] = (
            f"`{module_path}/pom.xml` does not configure JaCoCo, so AgentShield could not generate a "
            "coverage step."
        )
    return reasons


def _explain_missing_go_checks(module_path: str, project_root: Path) -> dict[str, str]:
    facts = _load_go_module_facts(project_root, module_path)
    if facts is None or not facts.has_module_file:
        return {}
    return {}


def explain_missing_standard_checks(module_path: str, project_root: Path) -> dict[str, str]:
    if (project_root / module_path / "go.mod").exists():
        return _explain_missing_go_checks(module_path, project_root)
    if (project_root / module_path / "package.json").exists():
        return _explain_missing_node_checks(module_path, project_root)
    if (project_root / module_path / "pyproject.toml").exists():
        return _explain_missing_python_checks(module_path, project_root)
    if _resolve_python_module_context(project_root, module_path) is not None:
        return _explain_missing_python_checks(module_path, project_root)
    if (project_root / module_path / "pom.xml").exists():
        return _explain_missing_java_checks(module_path, project_root)
    return {}


def build_preset_checks(module: ScanModuleSuggestion, project_root: Path) -> list[CheckConfig]:
    module_path = module.path or module.name or "."
    if (project_root / module_path / "go.mod").exists():
        return _build_go_checks(module_path, project_root)
    if (project_root / module_path / "pom.xml").exists():
        return _build_java_maven_checks(module_path, project_root)
    if (project_root / module_path / "pyproject.toml").exists():
        return _build_python_checks(module_path, project_root)
    if (project_root / module_path / "package.json").exists():
        return _build_node_checks(module_path, project_root)
    key = _module_key(module)
    if key == "go":
        return _build_go_checks(module_path, project_root)
    if key == "java-maven":
        return _build_java_maven_checks(module_path, project_root)
    if key == "python":
        return _build_python_checks(module_path, project_root)
    if key == "node":
        return _build_node_checks(module_path, project_root)
    return []
