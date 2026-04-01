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
    root_prefix = Path(*([".."] * len(Path(module_path).parts)))
    return (root_prefix / ".qa-agent" / "generated" / Path(*parts)).as_posix()


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


def _is_placeholder_test_script(script: str) -> bool:
    lowered = script.lower()
    if any(marker in lowered for marker in PLACEHOLDER_TEST_MARKERS):
        return True
    return re.search(r"\bno\b.*\btests?\b", lowered) is not None


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


def _python_uv_run_prefix(facts: PythonModuleFacts, required_tools: set[str]) -> list[str]:
    prefix = ["uv", "run"]
    extras = sorted(
        group_name
        for group_name, dependencies in facts.optional_dependency_groups.items()
        if group_name in PYTHON_TOOL_GROUPS and required_tools & dependencies
    )
    for extra in extras:
        prefix.extend(["--extra", extra])
    return prefix


def _build_node_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    facts = _load_node_module_facts(project_root, module_path)
    if facts is None:
        return []

    checks: list[CheckConfig] = []
    for kind, script_name in NODE_SCRIPT_CHECKS:
        if script_name not in facts.scripts:
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

    test_script = facts.scripts.get("test")
    if test_script and not _is_placeholder_test_script(test_script):
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "test"),
                label=f"{module_path} - test",
                module=module_path,
                kind="test",
                argv=_package_manager_run_argv(facts.package_manager, "test"),
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
        coverage_dir = _relative_generated_path(module_path, "coverage", _slug(module_path))
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

    return checks


def _build_python_checks(module_path: str, project_root: Path) -> list[CheckConfig]:
    facts = _load_python_module_facts(project_root, module_path)
    if facts is None:
        return []

    checks: list[CheckConfig] = []
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
                cwd=module_path,
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
                cwd=module_path,
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
                cwd=module_path,
            )
        )

    if "pyright" in facts.all_dependencies:
        type_targets = facts.pyright_include or facts.source_paths + facts.test_paths or ["."]
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=[*_python_uv_run_prefix(facts, {"pyright"}), "pyright", *type_targets],
                cwd=module_path,
            )
        )
    elif "mypy" in facts.all_dependencies:
        type_targets = facts.source_paths or ["."]
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "typecheck"),
                label=f"{module_path} - typecheck",
                module=module_path,
                kind="typecheck",
                argv=[*_python_uv_run_prefix(facts, {"mypy"}), "mypy", *type_targets],
                cwd=module_path,
            )
        )

    pytest_args = facts.test_paths or ["tests"]
    if "pytest" in facts.all_dependencies:
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "test"),
                label=f"{module_path} - test",
                module=module_path,
                kind="test",
                argv=[*_python_uv_run_prefix(facts, {"pytest"}), "pytest", *pytest_args],
                cwd=module_path,
                timeout_sec=1800,
            )
        )

    if "pytest" in facts.all_dependencies and "pytest-cov" in facts.all_dependencies and facts.source_paths:
        coverage_target = facts.source_paths[0]
        coverage_file = _relative_generated_path(module_path, "coverage", _slug(module_path), "coverage.json")
        checks.append(
            CheckConfig(
                id=_check_id(module_path, "coverage"),
                label=f"{module_path} - coverage",
                module=module_path,
                kind="coverage",
                argv=[
                    *_python_uv_run_prefix(facts, {"pytest", "pytest-cov"}),
                    "pytest",
                    f"--cov={coverage_target}",
                    f"--cov-report=json:{coverage_file}",
                    *pytest_args,
                ],
                cwd=module_path,
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

    reasons: dict[str, str] = {}
    test_script = facts.scripts.get("test")
    if test_script is None:
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
    if "vitest" not in dependency_names:
        reasons["coverage"] = (
            f"`{module_path}/package.json` does not include `vitest`, so AgentShield could not generate "
            "a JS coverage step."
        )
    elif not any(package_name in dependency_names for package_name in VITEST_COVERAGE_PACKAGES):
        reasons["coverage"] = (
            f"`{module_path}/package.json` does not include `@vitest/coverage-v8` or "
            "`@vitest/coverage-istanbul`, so AgentShield could not generate a coverage step."
        )

    return reasons


def _explain_missing_python_checks(module_path: str, project_root: Path) -> dict[str, str]:
    facts = _load_python_module_facts(project_root, module_path)
    if facts is None:
        return {}

    reasons: dict[str, str] = {}
    if not facts.has_build_system:
        reasons["build"] = (
            f"`{module_path}/pyproject.toml` does not define a build system, so AgentShield could not "
            "generate a build step."
        )
    if "ruff" not in facts.all_dependencies and "black" not in facts.all_dependencies:
        reasons["lint"] = (
            f"`{module_path}/pyproject.toml` does not include `ruff` or `black` in dependencies or optional "
            "dependency groups, so AgentShield could not generate a lint step."
        )
    if "pyright" not in facts.all_dependencies and "mypy" not in facts.all_dependencies:
        reasons["typecheck"] = (
            f"`{module_path}/pyproject.toml` does not include `pyright` or `mypy`, so AgentShield could not "
            "generate a typecheck step."
        )
    if "pytest" not in facts.all_dependencies:
        reasons["test"] = (
            f"`{module_path}/pyproject.toml` does not include `pytest`, so AgentShield could not generate "
            "a test step."
        )
    if "pytest" not in facts.all_dependencies:
        reasons["coverage"] = (
            f"`{module_path}/pyproject.toml` does not include `pytest`, so AgentShield could not generate "
            "a coverage step."
        )
    elif "pytest-cov" not in facts.all_dependencies:
        reasons["coverage"] = (
            f"`{module_path}/pyproject.toml` does not include `pytest-cov`, so AgentShield could not "
            "generate a coverage step."
        )
    elif not facts.source_paths:
        reasons["coverage"] = (
            f"`{module_path}/pyproject.toml` does not expose a detectable source package path, so AgentShield "
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
