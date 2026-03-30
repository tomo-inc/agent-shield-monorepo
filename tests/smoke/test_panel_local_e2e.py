from __future__ import annotations

import json
import os
import subprocess
import textwrap
import time
from pathlib import Path


REPO_ROOT = Path("/Users/xiaoxiong/Documents/work/tomo/workCode/AgentShield/agent-shield-monorepo")
CLI_PROJECT = REPO_ROOT / "packages" / "cli"
CLI_PYTHON = CLI_PROJECT / ".venv" / "bin" / "python"
PANEL_BASE_URL = "http://127.0.0.1:8000"
POSTGRES_CONTAINER = "agentshield-postgres"
POSTGRES_DB = "agentshield_panel_dev"
POSTGRES_USER = "agentshield"


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=merged_env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _ensure_local_runtime() -> None:
    health = _run(["curl", "-s", f"{PANEL_BASE_URL}/healthz"], cwd=REPO_ROOT)
    if health.returncode != 0:
        raise AssertionError(f"panel api health check failed: {health.stderr or health.stdout}")
    payload = json.loads(health.stdout)
    if payload.get("status") != "ok":
        raise AssertionError(f"panel api is unhealthy: {health.stdout}")

    services = _run(["docker", "compose", "ps"], cwd=REPO_ROOT)
    if services.returncode != 0:
        raise AssertionError(f"docker compose ps failed: {services.stderr or services.stdout}")
    if "agentshield-api" not in services.stdout or "agentshield-postgres" not in services.stdout:
        raise AssertionError(f"required local services are missing:\n{services.stdout}")


def _curl_json(path: str) -> dict[str, object]:
    response = _run(["curl", "-s", f"{PANEL_BASE_URL}{path}"], cwd=REPO_ROOT)
    if response.returncode != 0:
        raise AssertionError(response.stderr or response.stdout)
    return json.loads(response.stdout)


def _psql_scalar(sql: str) -> str:
    result = _run(
        [
            "docker",
            "exec",
            POSTGRES_CONTAINER,
            "psql",
            "-U",
            POSTGRES_USER,
            "-d",
            POSTGRES_DB,
            "-t",
            "-A",
            "-c",
            sql,
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def _build_init_wrapper(repo_dir: Path, project_key: str) -> Path:
    wrapper = repo_dir / "run_init_smoke.py"
    coverage_program = (
        "from pathlib import Path; "
        "Path('.qa-agent/generated/coverage/service/coverage.json').parent.mkdir(parents=True, exist_ok=True); "
        "Path('.qa-agent/generated/coverage/service/coverage.json').write_text("
        "'{\"totals\": {\"percent_covered\": 100.0}}', encoding='utf-8')"
    )
    wrapper.write_text(
        textwrap.dedent(
            f"""
            from __future__ import annotations

            import yaml
            from pathlib import Path

            import agentshield_cli.cli as cli
            from agentshield_cli.config import AgentShieldConfig, CheckConfig, ProjectConfig
            from agentshield_cli.models import ScanModuleSuggestion, ScanReport


            def fake_initialize_project(*, bootstrap_config, config_path, used_config_file):
                del bootstrap_config, used_config_file
                checks = [
                    CheckConfig(id="service-build", label="service - build", module="service", kind="build", argv=["python", "-c", "print('build ok')"]),
                    CheckConfig(id="service-lint", label="service - lint", module="service", kind="lint", argv=["python", "-c", "print('lint ok')"]),
                    CheckConfig(id="service-typecheck", label="service - typecheck", module="service", kind="typecheck", argv=["python", "-c", "print('typecheck ok')"]),
                    CheckConfig(id="service-test", label="service - test", module="service", kind="test", argv=["python", "-c", "print('test ok')"]),
                    CheckConfig(
                        id="service-coverage",
                        label="service - coverage",
                        module="service",
                        kind="coverage",
                        argv=["python", "-c", {coverage_program!r}],
                        coverage_parser="coverage.py-json",
                        coverage_file=".qa-agent/generated/coverage/service/coverage.json",
                    ),
                ]
                config = AgentShieldConfig(project=ProjectConfig(name={project_key!r}, root="."), checks=checks)
                payload = {{
                    "version": 1,
                    "project": {{"name": {project_key!r}, "root": "."}},
                    "checks": [check.model_dump(mode="json", exclude_none=True) for check in checks],
                }}
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
                return config, ScanReport(
                    project_name={project_key!r},
                    project_type="python",
                    summary="panel smoke",
                    modules=[ScanModuleSuggestion(name="service", path="service", language="Python", confidence=1.0)],
                )


            cli.initialize_project = fake_initialize_project
            raise SystemExit(cli.main(["init", "--yes"]))
            """
        ),
        encoding="utf-8",
    )
    return wrapper


def test_panel_write_path_e2e(tmp_path: Path) -> None:
    _ensure_local_runtime()

    project_key = f"panel-smoke-{int(time.time())}"
    repo_dir = tmp_path / project_key
    repo_dir.mkdir(parents=True)
    (repo_dir / "service").mkdir()

    env = {"AGENTSHIELD_PANEL_BASE_URL": PANEL_BASE_URL}

    init_wrapper = _build_init_wrapper(repo_dir, project_key)
    init_result = _run([str(CLI_PYTHON), str(init_wrapper)], cwd=repo_dir, env=env)
    assert init_result.returncode == 0, init_result.stderr or init_result.stdout
    assert "Panel sync: project register ok" in init_result.stdout
    assert "Panel sync: baselines ok" in init_result.stdout

    detail_after_init = _curl_json(f"/api/v1/panel/projects/{project_key}")
    assert detail_after_init["project"]["project_key"] == project_key
    assert detail_after_init["project"]["onboarding_status"] == "ready"
    assert detail_after_init["project"]["latest_run"] is None

    project_row = _psql_scalar(
        f"select onboarding_status from panel_projects where project_key='{project_key}';"
    )
    assert project_row == "ready"
    baseline_row = _psql_scalar(
        "select baseline_pct from panel_baselines b "
        "join panel_modules m on m.id = b.module_id "
        f"where m.project_id = (select id from panel_projects where project_key='{project_key}') "
        "and m.module_name = 'service';"
    )
    assert baseline_row == "100"

    baseline_result = _run(
        [
            "uv",
            "run",
            "--project",
            str(CLI_PROJECT),
            "agentshield",
            "baseline",
            "update",
        ],
        cwd=repo_dir,
        env=env,
        input_text="y\n",
    )
    assert baseline_result.returncode == 0, baseline_result.stderr or baseline_result.stdout
    assert "Panel sync: baselines ok" in baseline_result.stdout

    check_result = _run(
        [
            "uv",
            "run",
            "--project",
            str(CLI_PROJECT),
            "agentshield",
            "check",
            "--strict",
        ],
        cwd=repo_dir,
        env=env,
    )
    assert check_result.returncode == 0, check_result.stderr or check_result.stdout
    assert "Panel sync: run ok" in check_result.stdout

    latest = _curl_json(f"/api/v1/panel/projects/{project_key}/latest")
    assert latest["run"]["status"] == "pass"
    assert latest["run"]["strict_mode"] is True
    assert len(latest["run"]["modules"]) == 1
    assert latest["run"]["modules"][0]["module_name"] == "service"
    assert latest["run"]["modules"][0]["coverage_pct"] == 100.0
    assert latest["run"]["modules"][0]["baseline_pct"] == 100.0
    assert latest["run"]["modules"][0]["coverage_delta_pct"] == 0.0
    assert len(latest["run"]["modules"][0]["checker_results"]) == 5

    run_count = _psql_scalar(
        f"select count(*) from panel_runs where project_id=(select id from panel_projects where project_key='{project_key}');"
    )
    assert run_count == "1"
    run_module_count = _psql_scalar(
        "select count(*) from panel_run_modules where run_id=("
        "select id from panel_runs where project_id=("
        f"select id from panel_projects where project_key='{project_key}') order by id desc limit 1);"
    )
    assert run_module_count == "1"
    checker_count = _psql_scalar(
        "select count(*) from panel_checker_results where run_id=("
        "select id from panel_runs where project_id=("
        f"select id from panel_projects where project_key='{project_key}') order by id desc limit 1);"
    )
    assert checker_count == "5"
