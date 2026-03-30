from __future__ import annotations

import re
from pathlib import Path

from agentshield_cli.config import CheckConfig
from agentshield_cli.models import ScanModuleSuggestion


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _module_key(module: ScanModuleSuggestion) -> str:
    path = module.path.lower()
    frameworks = {item.lower() for item in module.frameworks}
    if path == "apps/api" or "fastapi" in frameworks:
        return "python-api"
    if path == "apps/web" or "next.js" in frameworks or "nextjs" in frameworks:
        return "nextjs-web"
    if path == "packages/cli":
        return "python-cli"
    if module.language.lower() == "python":
        return "python-generic"
    if module.language.lower() in {"typescript", "javascript"}:
        return "node-generic"
    return "fallback"


def _check_id(module_path: str, kind: str) -> str:
    return f"{_slug(module_path)}-{_slug(kind)}"


def _python_api_checks(module_path: str) -> list[CheckConfig]:
    return [
        CheckConfig(
            id=_check_id(module_path, "build"),
            label=f"{module_path} - build",
            module=module_path,
            kind="build",
            argv=["uv", "build", "."],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "lint"),
            label=f"{module_path} - lint",
            module=module_path,
            kind="lint",
            argv=["uv", "run", "--extra", "dev", "ruff", "check", "app", "tests"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "typecheck"),
            label=f"{module_path} - typecheck",
            module=module_path,
            kind="typecheck",
            argv=["uv", "run", "--extra", "dev", "pyright", "app", "tests"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "test"),
            label=f"{module_path} - test",
            module=module_path,
            kind="test",
            argv=["uv", "run", "--extra", "dev", "pytest", "tests"],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "coverage"),
            label=f"{module_path} - coverage",
            module=module_path,
            kind="coverage",
            argv=[
                "uv",
                "run",
                "--extra",
                "dev",
                "pytest",
                "--cov=app",
                "--cov-report=json:../../.qa-agent/generated/coverage/apps-api/coverage.json",
                "tests",
            ],
            cwd=module_path,
            coverage_parser="coverage.py-json",
            coverage_file="../../.qa-agent/generated/coverage/apps-api/coverage.json",
            timeout_sec=1800,
        ),
    ]


def _nextjs_web_checks(module_path: str) -> list[CheckConfig]:
    return [
        CheckConfig(
            id=_check_id(module_path, "build"),
            label=f"{module_path} - build",
            module=module_path,
            kind="build",
            argv=["pnpm", "build"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "lint"),
            label=f"{module_path} - lint",
            module=module_path,
            kind="lint",
            argv=["pnpm", "lint"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "typecheck"),
            label=f"{module_path} - typecheck",
            module=module_path,
            kind="typecheck",
            argv=["pnpm", "typecheck"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "test"),
            label=f"{module_path} - test",
            module=module_path,
            kind="test",
            argv=["pnpm", "test"],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "coverage"),
            label=f"{module_path} - coverage",
            module=module_path,
            kind="coverage",
            argv=[
                "pnpm",
                "exec",
                "vitest",
                "run",
                "--coverage.enabled=true",
                "--coverage.provider=v8",
                "--coverage.reporter=json-summary",
                "--coverage.reporter=text",
                "--coverage.reportsDirectory=../../.qa-agent/generated/coverage/apps-web",
            ],
            cwd=module_path,
            coverage_parser="istanbul-summary",
            coverage_file="../../.qa-agent/generated/coverage/apps-web/coverage-summary.json",
            timeout_sec=1800,
        ),
    ]


def _python_cli_checks(module_path: str) -> list[CheckConfig]:
    return [
        CheckConfig(
            id=_check_id(module_path, "build"),
            label=f"{module_path} - build",
            module=module_path,
            kind="build",
            argv=["uv", "build", "."],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "lint"),
            label=f"{module_path} - lint",
            module=module_path,
            kind="lint",
            argv=["uv", "run", "--extra", "dev", "ruff", "check", "agentshield_cli", "tests"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "typecheck"),
            label=f"{module_path} - typecheck",
            module=module_path,
            kind="typecheck",
            argv=["uv", "run", "--extra", "dev", "pyright", "agentshield_cli", "tests"],
            cwd=module_path,
        ),
        CheckConfig(
            id=_check_id(module_path, "test"),
            label=f"{module_path} - test",
            module=module_path,
            kind="test",
            argv=["uv", "run", "--extra", "dev", "pytest", "tests"],
            cwd=module_path,
            timeout_sec=1800,
        ),
        CheckConfig(
            id=_check_id(module_path, "coverage"),
            label=f"{module_path} - coverage",
            module=module_path,
            kind="coverage",
            argv=[
                "uv",
                "run",
                "--extra",
                "dev",
                "pytest",
                "--cov=agentshield_cli",
                "--cov-report=json:../../.qa-agent/generated/coverage/packages-cli/coverage.json",
                "tests",
            ],
            cwd=module_path,
            coverage_parser="coverage.py-json",
            coverage_file="../../.qa-agent/generated/coverage/packages-cli/coverage.json",
            timeout_sec=1800,
        ),
    ]


def _fallback_checks(module: ScanModuleSuggestion) -> list[CheckConfig]:
    module_path = module.path or module.name or "."
    checks: list[CheckConfig] = []
    for suggestion in module.recommended_checks:
        argv = suggestion.resolved_argv()
        if not argv:
            continue
        checks.append(
            CheckConfig(
                id=_check_id(module_path, suggestion.id),
                label=f"{module_path} - {suggestion.id}",
                module=module_path,
                kind="custom",
                argv=argv,
                cwd=suggestion.cwd,
                timeout_sec=1800 if "test" in suggestion.id.lower() else 1200,
            )
        )
    return checks


def build_preset_checks(module: ScanModuleSuggestion, project_root: Path) -> list[CheckConfig]:
    del project_root
    module_path = module.path or module.name or "."
    key = _module_key(module)
    if key == "python-api":
        return _python_api_checks(module_path)
    if key == "nextjs-web":
        return _nextjs_web_checks(module_path)
    if key == "python-cli":
        return _python_cli_checks(module_path)
    return _fallback_checks(module)
