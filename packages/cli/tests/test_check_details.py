from __future__ import annotations

import json
from pathlib import Path

from agentshield_cli.check_details import select_failure_reason
from agentshield_cli.models import CheckResult


def test_select_failure_reason_detects_node_dependency_install_drift(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "packageManager": "pnpm@10.11.0"}),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "devDependencies": {
                    "happy-dom": "^20.8.9",
                },
            }
        ),
        encoding="utf-8",
    )

    check = CheckResult(
        id="apps-web-test",
        label="apps/web - test",
        module="apps/web",
        kind="test",
        command="pnpm run test",
        status="fail",
        exit_code=1,
        duration_sec=0.2,
        stdout_tail=["MISSING DEPENDENCY  Cannot find dependency 'happy-dom'"],
    )

    reason = select_failure_reason(check, project_root=tmp_path)

    assert reason == (
        "`happy-dom` is declared in `apps/web/package.json` but is not installed in the current "
        "workspace. Run `pnpm install --frozen-lockfile` from the repo root to sync dependencies."
    )


def test_select_failure_reason_detects_typescript_module_install_drift(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "packageManager": "pnpm@10.11.0"}),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "devDependencies": {
                    "@testing-library/react": "^16.3.2",
                },
            }
        ),
        encoding="utf-8",
    )

    check = CheckResult(
        id="apps-web-typecheck",
        label="apps/web - typecheck",
        module="apps/web",
        kind="typecheck",
        command="pnpm run typecheck",
        status="fail",
        exit_code=1,
        duration_sec=0.2,
        stderr_tail=[
            "src/example.test.tsx(2,32): error TS2307: Cannot find module '@testing-library/react' or its corresponding type declarations."
        ],
    )

    reason = select_failure_reason(check, project_root=tmp_path)

    assert reason == (
        "`@testing-library/react` is declared in `apps/web/package.json` but is not installed in the current "
        "workspace. Run `pnpm install --frozen-lockfile` from the repo root to sync dependencies."
    )


def test_select_failure_reason_keeps_raw_error_when_package_is_installed(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (module_root / "node_modules" / "happy-dom").mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "packageManager": "pnpm@10.11.0"}),
        encoding="utf-8",
    )
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "devDependencies": {
                    "happy-dom": "^20.8.9",
                },
            }
        ),
        encoding="utf-8",
    )

    check = CheckResult(
        id="apps-web-test",
        label="apps/web - test",
        module="apps/web",
        kind="test",
        command="pnpm run test",
        status="fail",
        exit_code=1,
        duration_sec=0.2,
        stderr_tail=["Error: Cannot find package 'happy-dom' imported from vitest"],
    )

    reason = select_failure_reason(check, project_root=tmp_path)

    assert reason == "Error: Cannot find package 'happy-dom' imported from vitest"


def test_select_failure_reason_detects_vitest_environment_install_drift(tmp_path: Path) -> None:
    module_root = tmp_path / "apps" / "web"
    module_root.mkdir(parents=True)
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "packageManager": "pnpm@10.11.0"}),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/web",
                "scripts": {"test": "vitest run"},
                "devDependencies": {
                    "happy-dom": "^20.8.9",
                    "vitest": "^3.2.4",
                },
            }
        ),
        encoding="utf-8",
    )
    (module_root / "vitest.config.mts").write_text(
        'export default { test: { environment: "happy-dom" } }\n',
        encoding="utf-8",
    )

    check = CheckResult(
        id="apps-web-test",
        label="apps/web - test",
        module="apps/web",
        kind="test",
        command="pnpm run test",
        status="fail",
        exit_code=1,
        duration_sec=0.2,
        stderr_tail=["Serialized Error: { code: 'ERR_MODULE_NOT_FOUND' }"],
    )

    reason = select_failure_reason(check, project_root=tmp_path)

    assert reason == (
        "`happy-dom` is declared in `apps/web/package.json` but is not installed in the current "
        "workspace. Run `pnpm install --frozen-lockfile` from the repo root to sync dependencies."
    )


def test_select_failure_reason_detects_standalone_module_binary_install_drift(tmp_path: Path) -> None:
    module_root = tmp_path / "auth"
    module_root.mkdir(parents=True)
    (module_root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (module_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@demo/auth",
                "packageManager": "pnpm@10.11.0",
                "dependencies": {
                    "next": "^15.0.0",
                },
            }
        ),
        encoding="utf-8",
    )

    check = CheckResult(
        id="auth-build",
        label="auth - build",
        module="auth",
        kind="build",
        command="pnpm run build",
        status="fail",
        exit_code=127,
        duration_sec=0.2,
        stderr_tail=["sh: next: command not found"],
    )

    reason = select_failure_reason(check, project_root=tmp_path)

    assert reason == (
        "`next` is declared in `auth/package.json` but is not installed in the current "
        "workspace. Run `pnpm install --frozen-lockfile` in `auth` to sync dependencies."
    )


def test_select_failure_reason_skips_generic_elifecycle_wrapper() -> None:
    check = CheckResult(
        id="auth-test",
        label="auth - test",
        module="auth",
        kind="test",
        command="pnpm run test:unit",
        status="fail",
        exit_code=1,
        duration_sec=0.5,
        stderr_tail=[
            "AssertionError [ERR_ASSERTION]: expected rejection",
            "✖ verifyRefreshToken rejects an internal JWT (type !== refresh) (1.22ms)",
            " ELIFECYCLE  Command failed with exit code 1.",
        ],
    )

    reason = select_failure_reason(check)

    assert reason == "✖ verifyRefreshToken rejects an internal JWT (type !== refresh) (1.22ms)"
