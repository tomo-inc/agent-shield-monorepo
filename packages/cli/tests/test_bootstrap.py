from __future__ import annotations

import json
from pathlib import Path

from agentshield_cli.bootstrap import (
    build_checks_from_scan_module,
    build_config_from_scan,
    normalize_scan_report,
)
from agentshield_cli.config import AgentShieldConfig
from agentshield_cli.models import RepoSnapshot, ScanCheckSuggestion, ScanModuleSuggestion, ScanReport
from agentshield_cli.presets import explain_missing_standard_checks


def _write_python_pyproject(path: Path, *, include_pyright_config: bool = True) -> None:
    pyright_block = ""
    if include_pyright_config:
        pyright_block = """

[tool.pyright]
include = ["src", "tests"]
"""
    path.write_text(
        (
            """
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "demo-api"
dependencies = ["fastapi>=0.1"]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov>=6", "pyright>=1", "ruff>=0.1"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
            + pyright_block
        ).strip(),
        encoding="utf-8",
    )


def _write_go_mod(path: Path) -> None:
    path.write_text(
        """
module github.com/demo/service

go 1.23.0
        """.strip(),
        encoding="utf-8",
    )


def _write_root_python_pyproject(path: Path, *, include_typecheck: bool = True, include_coverage: bool = True) -> None:
    dev_deps = ['"pytest>=8"']
    if include_coverage:
        dev_deps.append('"pytest-cov>=6"')
    if include_typecheck:
        dev_deps.extend(['"pyright>=1"', '"ruff>=0.1"'])
    path.write_text(
        f"""
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "demo-root"
dependencies = ["fastapi>=0.1"]

[project.optional-dependencies]
dev = [{", ".join(dev_deps)}]

[tool.pytest.ini_options]
testpaths = ["tests"]
        """.strip(),
        encoding="utf-8",
    )


def test_build_config_from_scan_prefers_deterministic_presets_and_keeps_ai_custom_checks(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "api"
    (module_root / "src").mkdir(parents=True)
    (module_root / "tests").mkdir()
    _write_python_pyproject(module_root / "pyproject.toml")

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
                frameworks=["fastapi"],
                confidence=0.9,
                recommended_checks=[
                    ScanCheckSuggestion(id="build", argv=["python", "-m", "compileall", "src"]),
                    ScanCheckSuggestion(id="lint", argv=["ruff", "check", "."]),
                    ScanCheckSuggestion(id="test", argv=["pytest"]),
                    ScanCheckSuggestion(id="security-scan", argv=["python", "-m", "bandit", "-r", "src"]),
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
    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage", "custom"]
    assert config.checks[0].argv == ["uv", "build", "."]
    assert config.checks[0].cwd == "apps/api"
    assert config.checks[1].argv == ["uv", "run", "--extra", "dev", "ruff", "check", "src", "tests"]
    assert config.checks[2].argv == ["uv", "run", "--extra", "dev", "pyright", "src", "tests"]
    assert config.checks[3].argv == ["uv", "run", "--extra", "dev", "pytest", "tests"]
    assert config.checks[4].argv == [
        "uv",
        "run",
        "--extra",
        "dev",
        "pytest",
        "--cov=src",
        "--cov-report=json:../../.qa-agent/generated/coverage/apps-api/coverage.json",
        "tests",
    ]
    assert config.checks[5].kind == "custom"
    assert config.checks[5].argv == ["python", "-m", "bandit", "-r", "src"]
    assert config.checks[5].cwd == "apps/api"
    assert "llm" not in payload


def test_build_checks_from_scan_module_normalizes_rust_custom_subcommands(tmp_path: Path) -> None:
    module = ScanModuleSuggestion(
        name="merchant",
        path="src/merchant",
        language="Rust",
        confidence=0.9,
        recommended_checks=[
            ScanCheckSuggestion(id="style", argv=["clippy", "--bin", "merchant"]),
            ScanCheckSuggestion(id="smoke", argv=["test", "--bin", "merchant"]),
        ],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert len(checks) == 2
    assert [check.kind for check in checks] == ["custom", "custom"]
    assert checks[0].argv == ["cargo", "clippy", "--bin", "merchant"]
    assert checks[1].argv == ["cargo", "test", "--bin", "merchant"]


def test_build_checks_from_scan_module_uses_java_preset_for_apps_api(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "api"
    module_root.mkdir(parents=True)
    (module_root / "pom.xml").write_text(
        """
        <project>
          <build>
            <plugins>
              <plugin><artifactId>spotless-maven-plugin</artifactId></plugin>
              <plugin><artifactId>jacoco-maven-plugin</artifactId></plugin>
            </plugins>
          </build>
        </project>
        """,
        encoding="utf-8",
    )
    module = ScanModuleSuggestion(
        name="api",
        path="apps/api",
        language="Java",
        frameworks=["Spring Boot"],
        confidence=0.9,
        recommended_checks=[
            ScanCheckSuggestion(id="build", argv=["mvn", "clean", "install"]),
            ScanCheckSuggestion(id="test", argv=["mvn", "test"]),
        ],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert [check.kind for check in checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert checks[0].argv == ["mvn", "-B", "-DskipTests", "package"]
    assert checks[1].argv == ["mvn", "-B", "spotless:check"]
    assert checks[2].argv == ["mvn", "-B", "-DskipTests", "compile"]
    assert checks[3].argv == ["mvn", "-B", "test"]
    assert checks[4].argv == ["mvn", "-B", "test", "jacoco:report"]
    assert checks[4].coverage_parser == "jacoco-xml"
    assert checks[4].coverage_file == "."


def test_build_checks_from_scan_module_inherits_root_python_manifest_for_submodule(tmp_path: Path) -> None:
    (tmp_path / "infer" / "auth").mkdir(parents=True)
    (tmp_path / "infer" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "infer" / "auth" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "auth").mkdir(parents=True)
    _write_root_python_pyproject(tmp_path / "pyproject.toml")

    module = ScanModuleSuggestion(
        name="auth",
        path="infer/auth",
        language="python",
        frameworks=["fastapi"],
        confidence=0.93,
        recommended_checks=[],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert [check.kind for check in checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert checks[0].argv == ["uv", "build", "."]
    assert checks[0].cwd == "."
    assert checks[1].argv == ["uv", "run", "--extra", "dev", "ruff", "check", "infer/auth", "tests/auth"]
    assert checks[1].cwd == "."
    assert checks[2].argv == ["uv", "run", "--extra", "dev", "pyright", "infer/auth"]
    assert checks[2].cwd == "."
    assert checks[3].argv == ["uv", "run", "--extra", "dev", "pytest", "tests/auth"]
    assert checks[3].cwd == "."
    assert checks[4].argv == [
        "uv",
        "run",
        "--extra",
        "dev",
        "pytest",
        "--cov=infer/auth",
        "--cov-report=json:.qa-agent/generated/coverage/infer-auth/coverage.json",
        "tests/auth",
    ]
    assert checks[4].coverage_file == ".qa-agent/generated/coverage/infer-auth/coverage.json"
    assert checks[4].cwd == "."


def test_build_checks_from_scan_module_inherits_root_python_manifest_with_fallback_tools(
    tmp_path: Path,
) -> None:
    (tmp_path / "infer" / "auth").mkdir(parents=True)
    (tmp_path / "infer" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "infer" / "auth" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "auth").mkdir(parents=True)
    _write_root_python_pyproject(tmp_path / "pyproject.toml", include_typecheck=False, include_coverage=False)

    module = ScanModuleSuggestion(
        name="auth",
        path="infer/auth",
        language="python",
        frameworks=["fastapi"],
        confidence=0.93,
        recommended_checks=[],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert [check.kind for check in checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert checks[0].argv == ["uv", "build", "."]
    assert checks[0].cwd == "."
    assert checks[1].argv == ["uv", "run", "--with", "ruff", "ruff", "check", "infer/auth", "tests/auth"]
    assert checks[1].cwd == "."
    assert checks[2].argv == ["uv", "run", "--with", "pyright", "pyright", "infer/auth"]
    assert checks[2].cwd == "."
    assert checks[3].argv == ["uv", "run", "--extra", "dev", "pytest", "tests/auth"]
    assert checks[3].cwd == "."
    assert checks[4].argv == [
        "uv",
        "run",
        "--extra",
        "dev",
        "--with",
        "pytest-cov",
        "pytest",
        "--cov=infer/auth",
        "--cov-report=json:.qa-agent/generated/coverage/infer-auth/coverage.json",
        "tests/auth",
    ]
    assert checks[4].coverage_file == ".qa-agent/generated/coverage/infer-auth/coverage.json"
    assert checks[4].cwd == "."


def test_build_checks_from_scan_module_does_not_inherit_root_python_manifest_for_unrelated_submodule(
    tmp_path: Path,
) -> None:
    (tmp_path / "infer").mkdir()
    (tmp_path / "infer" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tests").mkdir()
    _write_root_python_pyproject(tmp_path / "pyproject.toml")

    module = ScanModuleSuggestion(
        name="scripts",
        path="scripts",
        language="python",
        confidence=0.9,
        recommended_checks=[],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert checks == []


def test_build_checks_from_scan_module_defaults_python_typecheck_to_source_paths(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "api"
    (module_root / "src").mkdir(parents=True)
    (module_root / "tests").mkdir()
    _write_python_pyproject(module_root / "pyproject.toml", include_pyright_config=False)

    module = ScanModuleSuggestion(
        name="api",
        path="apps/api",
        language="python",
        frameworks=["fastapi"],
        confidence=0.95,
        recommended_checks=[],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert [check.kind for check in checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert checks[2].argv == ["uv", "run", "--extra", "dev", "pyright", "src"]


def test_explain_missing_standard_checks_skips_inherited_python_fallback_reasons(tmp_path: Path) -> None:
    (tmp_path / "infer" / "auth").mkdir(parents=True)
    (tmp_path / "infer" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "infer" / "auth" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "auth").mkdir(parents=True)
    _write_root_python_pyproject(tmp_path / "pyproject.toml", include_typecheck=False, include_coverage=False)

    reasons = explain_missing_standard_checks("infer/auth", tmp_path)

    assert reasons == {}


def test_build_config_from_scan_excludes_test_only_modules(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "api"
    (module_root / "src").mkdir(parents=True)
    (module_root / "tests").mkdir()
    _write_python_pyproject(module_root / "pyproject.toml")

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
                frameworks=["fastapi"],
                confidence=0.95,
                recommended_checks=[],
            ),
            ScanModuleSuggestion(
                name="tests",
                path="tests",
                language="python",
                confidence=0.9,
                recommended_checks=[],
            ),
        ],
    )

    config, _ = build_config_from_scan(
        report,
        project_root=tmp_path,
        existing_config=existing,
        include_llm=False,
        include_notify=False,
    )

    assert {check.module for check in config.checks} == {"apps/api"}


def test_normalize_scan_report_flattens_rust_bin_file_paths() -> None:
    snapshot = RepoSnapshot(
        root=".",
        tree=["src/", "src/bin/", "src/bin/merchant.rs", "src/merchant/"],
        files=[],
    )
    report = ScanReport(
        project_name="demo-repo",
        project_type="rust",
        summary="demo",
        modules=[
            ScanModuleSuggestion(
                name="src/bin/merchant.rs",
                path="src/bin/merchant.rs",
                language="Rust",
                confidence=0.95,
                recommended_checks=[],
            )
        ],
    )

    normalized = normalize_scan_report(report, snapshot)

    assert normalized.modules[0].path == "src/merchant"
    assert normalized.modules[0].name == "merchant"


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


def test_build_config_from_scan_allows_incomplete_generated_quality_gate(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "scripts": {
                    "build": "next build",
                    "lint": "eslint . --max-warnings=0",
                    "typecheck": "tsc --noEmit",
                    "test": 'echo "No web tests yet"',
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="web",
                    path="apps/web",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.9,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, True, True, False, False]
    assert config.checks[0].argv == ["npm", "run", "build"]
    assert config.checks[1].argv == ["npm", "run", "lint"]
    assert config.checks[2].argv == ["npm", "run", "typecheck"]


def test_build_config_from_scan_prefers_test_unit_script_for_node_builtin_coverage(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "packageManager": "pnpm@10.11.0",
                "scripts": {
                    "build": "next build",
                    "lint": "next lint",
                    "test:unit": "node --test tests/*.test.cjs",
                    "test:auth": "node scripts/verify-auth.mjs",
                    "test:ui": "playwright test",
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="web",
                    path="apps/web",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.9,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, False, False, True, True]
    assert config.checks[0].argv == ["pnpm", "run", "build"]
    assert config.checks[1].argv == ["true"]
    assert config.checks[3].argv == ["pnpm", "run", "test:unit"]
    assert config.checks[4].argv == [
        "pnpm",
        "dlx",
        "c8@10.1.3",
        "--reporter=json-summary",
        "--reporter=text",
        "--reports-dir",
        "../../.qa-agent/generated/coverage/apps-web",
        "pnpm",
        "run",
        "test:unit",
    ]
    assert config.checks[4].coverage_parser == "istanbul-summary"
    assert config.checks[4].coverage_file == "../../.qa-agent/generated/coverage/apps-web/coverage-summary.json"


def test_build_config_from_scan_generates_typecheck_from_typescript_and_tsconfig(tmp_path: Path) -> None:
    module_root = tmp_path / "auth"
    module_root.mkdir(parents=True)
    (module_root / "tsconfig.json").write_text('{"compilerOptions":{"noEmit":true}}\n', encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/auth",
                "packageManager": "pnpm@10.11.0",
                "scripts": {
                    "build": "next build",
                    "lint": "next lint",
                    "test:unit": "node --experimental-strip-types --test tests/*.test.cjs",
                },
                "dependencies": {
                    "next": "^15.0.0",
                    "react": "^19.0.0",
                },
                "devDependencies": {
                    "typescript": "^5.7.0",
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="auth",
                    path="auth",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.95,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, False, True, True, True]
    assert config.checks[0].argv == ["pnpm", "run", "build"]
    assert config.checks[1].argv == ["true"]
    assert config.checks[2].argv == ["pnpm", "exec", "tsc", "--noEmit"]
    assert config.checks[3].argv == ["pnpm", "run", "test:unit"]
    assert config.checks[4].argv == [
        "pnpm",
        "dlx",
        "c8@10.1.3",
        "--reporter=json-summary",
        "--reporter=text",
        "--reports-dir",
        "../.qa-agent/generated/coverage/auth",
        "pnpm",
        "run",
        "test:unit",
    ]


def test_build_config_from_scan_generates_lint_from_next_and_eslint_config(tmp_path: Path) -> None:
    module_root = tmp_path / "auth"
    module_root.mkdir(parents=True)
    (module_root / "tsconfig.json").write_text('{"compilerOptions":{"noEmit":true}}\n', encoding="utf-8")
    (module_root / "eslint.config.mjs").write_text("export default [];\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/auth",
                "packageManager": "pnpm@10.11.0",
                "scripts": {
                    "build": "next build",
                    "test:unit": "node --experimental-strip-types --test tests/*.test.cjs",
                },
                "dependencies": {
                    "next": "^15.0.0",
                    "react": "^19.0.0",
                },
                "devDependencies": {
                    "eslint": "^9.0.0",
                    "typescript": "^5.7.0",
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="auth",
                    path="auth",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.95,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, True, True, True, True]
    assert config.checks[0].argv == ["pnpm", "run", "build"]
    assert config.checks[1].argv == ["pnpm", "exec", "next", "lint"]
    assert config.checks[2].argv == ["pnpm", "exec", "tsc", "--noEmit"]
    assert config.checks[3].argv == ["pnpm", "run", "test:unit"]
    assert config.checks[4].argv == [
        "pnpm",
        "dlx",
        "c8@10.1.3",
        "--reporter=json-summary",
        "--reporter=text",
        "--reports-dir",
        "../.qa-agent/generated/coverage/auth",
        "pnpm",
        "run",
        "test:unit",
    ]


def test_build_config_from_scan_uses_module_local_package_manager(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "portal"
    module_root.mkdir(parents=True)
    (tmp_path / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n", encoding="utf-8")
    (module_root / "bun.lockb").write_bytes(b"")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/portal",
                "packageManager": "bun@1.0.9",
                "scripts": {
                    "build": "next build",
                    "typecheck": "tsc --noEmit",
                    "test": "bun test",
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="portal",
                    path="apps/portal",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.95,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, False, True, True, False]
    assert config.checks[0].argv == ["bun", "run", "build"]
    assert config.checks[2].argv == ["bun", "run", "typecheck"]
    assert config.checks[3].argv == ["bun", "run", "test"]


def test_build_config_from_scan_falls_back_to_root_package_manager(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo-root", "packageManager": "pnpm@9.0.0"}),
        encoding="utf-8",
    )
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "scripts": {
                    "build": "next build",
                    "lint": "eslint . --max-warnings=0",
                    "typecheck": "tsc --noEmit",
                },
            }
        ),
        encoding="utf-8",
    )

    config, _ = build_config_from_scan(
        ScanReport(
            project_name="demo-repo",
            project_type="node",
            summary="demo",
            modules=[
                ScanModuleSuggestion(
                    name="web",
                    path="apps/web",
                    language="typescript",
                    frameworks=["next.js"],
                    confidence=0.95,
                    recommended_checks=[],
                )
            ],
        ),
        project_root=tmp_path,
        existing_config=AgentShieldConfig(),
        include_llm=False,
        include_notify=False,
    )

    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert [check.enabled for check in config.checks] == [True, True, True, False, False]
    assert config.checks[0].argv == ["pnpm", "run", "build"]
    assert config.checks[1].argv == ["pnpm", "run", "lint"]
    assert config.checks[2].argv == ["pnpm", "run", "typecheck"]


def test_build_checks_from_scan_module_uses_go_preset_for_go_modules(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "gateway"
    module_root.mkdir(parents=True)
    _write_go_mod(module_root / "go.mod")
    module = ScanModuleSuggestion(
        name="gateway",
        path="apps/gateway",
        language="Go",
        frameworks=["HTTP/JSON-RPC"],
        confidence=0.95,
        recommended_checks=[],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert [check.kind for check in checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert checks[0].argv == ["go", "build", "./..."]
    assert checks[1].argv == ["go", "vet", "./..."]
    assert checks[2].argv == ["go", "test", "-run", "^$", "./..."]
    assert checks[3].argv == ["go", "test", "./..."]
    assert checks[4].argv == [
        "go",
        "test",
        "-coverprofile=../../.qa-agent/generated/coverage/apps-gateway/coverage.out",
        "-covermode=count",
        "./...",
    ]
    assert checks[4].coverage_parser == "go-coverprofile"
    assert checks[4].coverage_file == "../../.qa-agent/generated/coverage/apps-gateway/coverage.out"
