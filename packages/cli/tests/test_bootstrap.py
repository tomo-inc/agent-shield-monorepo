from __future__ import annotations

from pathlib import Path

from agentshield_cli.bootstrap import (
    build_checks_from_scan_module,
    build_config_from_scan,
    normalize_scan_report,
)
from agentshield_cli.config import AgentShieldConfig
from agentshield_cli.models import ScanCheckSuggestion, ScanModuleSuggestion, ScanReport
from agentshield_cli.models import RepoSnapshot


def test_build_config_from_scan_prefers_ai_checks_and_fills_missing_defaults(tmp_path: Path) -> None:
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
                    ScanCheckSuggestion(id="build", run="python -m py_compile app"),
                    ScanCheckSuggestion(id="lint", run="ruff check ."),
                    ScanCheckSuggestion(id="test", argv=["pytest", "tests"]),
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
    assert [check.kind for check in config.checks] == ["build", "lint", "typecheck", "test", "coverage"]
    assert config.checks[0].run == "python -m py_compile app"
    assert config.checks[0].cwd == "apps/api"
    assert config.checks[1].run == "ruff check ."
    assert config.checks[1].cwd == "apps/api"
    assert config.checks[2].argv == ["uv", "run", "--extra", "dev", "pyright", "app", "tests"]
    assert config.checks[3].argv == ["pytest", "tests"]
    assert config.checks[-1].coverage_parser == "coverage.py-json"
    assert "llm" not in payload


def test_build_checks_from_scan_module_infers_coverage_metadata_without_preset(tmp_path: Path) -> None:
    module = ScanModuleSuggestion(
        name="service",
        path="service",
        language="python",
        confidence=0.8,
        recommended_checks=[
            ScanCheckSuggestion(
                id="coverage",
                argv=[
                    "pytest",
                    "--cov=service",
                    "--cov-report=json:.qa-agent/generated/coverage/service/coverage.json",
                    "tests",
                ],
            )
        ],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert len(checks) == 1
    assert checks[0].kind == "coverage"
    assert checks[0].coverage_parser == "coverage.py-json"
    assert checks[0].coverage_file == ".qa-agent/generated/coverage/service/coverage.json"


def test_build_checks_from_scan_module_normalizes_rust_subcommands(tmp_path: Path) -> None:
    module = ScanModuleSuggestion(
        name="merchant",
        path="src/merchant",
        language="Rust",
        confidence=0.9,
        recommended_checks=[
            ScanCheckSuggestion(id="lint", run="clippy --bin merchant"),
            ScanCheckSuggestion(id="test", run="test --bin merchant"),
        ],
    )

    checks = build_checks_from_scan_module(module, tmp_path)

    assert len(checks) == 2
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
    assert checks[0].argv == ["mvn", "clean", "install"]
    assert checks[0].cwd == "apps/api"
    assert checks[1].argv == ["mvn", "-B", "spotless:check"]
    assert checks[2].argv == ["mvn", "-B", "-DskipTests", "compile"]
    assert checks[3].argv == ["mvn", "test"]
    assert checks[4].argv == ["mvn", "-B", "test", "jacoco:report"]
    assert checks[4].coverage_parser == "jacoco-xml"
    assert checks[4].coverage_file == "."


def test_build_config_from_scan_excludes_test_only_modules(tmp_path: Path) -> None:
    existing = AgentShieldConfig()
    report = ScanReport(
        project_name="demo-repo",
        project_type="rust",
        summary="demo",
        modules=[
            ScanModuleSuggestion(
                name="merchant",
                path="src/merchant",
                language="Rust",
                confidence=0.95,
                recommended_checks=[
                    ScanCheckSuggestion(id="test", run="cargo test --bin merchant"),
                ],
            ),
            ScanModuleSuggestion(
                name="tests",
                path="tests",
                language="Rust",
                confidence=0.9,
                recommended_checks=[
                    ScanCheckSuggestion(id="test", run="cargo test --test e2e_mocker"),
                ],
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

    assert [check.module for check in config.checks] == ["src/merchant"]


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
