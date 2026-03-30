from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthz_returns_active_focus() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "api",
        "active_focus": "qa-automation",
    }


def test_capabilities_exposes_required_governance_files() -> None:
    response = client.get("/api/v1/capabilities")

    assert response.status_code == 200
    body = response.json()

    assert body["product"] == "AgentShield"
    assert "AGENTS.md" in body["required_files"]
    assert "skillscloud.md" in body["required_files"]


def test_list_panel_projects_returns_expected_envelope() -> None:
    response = client.get("/api/v1/panel/projects")

    assert response.status_code == 200
    body = response.json()

    assert body["generated_at"].endswith("Z")
    assert len(body["projects"]) == 2


def test_list_panel_projects_exposes_mock_project_fields() -> None:
    response = client.get("/api/v1/panel/projects")

    assert response.status_code == 200
    projects = response.json()["projects"]
    project = projects[0]
    second_project = projects[1]

    assert project == {
        "project_key": "agent-shield-monorepo",
        "project_name": "AgentShield Monorepo",
        "repo_path": "/workspace/agent-shield-monorepo",
        "preset": "infer-monorepo",
        "onboarding_status": "ready",
        "module_count": 2,
        "health": "failing",
        "source": "local-cli",
        "triggered_by": "dawei",
        "status": "fail",
        "block_reason": "apps/web coverage below gate",
        "started_at": "2026-03-30T10:00:00Z",
        "finished_at": "2026-03-30T10:00:31Z",
        "duration_sec": 31.0,
    }
    assert second_project["preset"] == "agentpay-sdk"
    assert second_project["module_count"] == 1
    assert second_project["health"] == "healthy"


def test_list_panel_projects_derives_module_count_and_health() -> None:
    response = client.get("/api/v1/panel/projects")

    assert response.status_code == 200
    projects = response.json()["projects"]
    projects_by_key = {project["project_key"]: project for project in projects}

    assert projects_by_key["agent-shield-monorepo"]["module_count"] == 2
    assert projects_by_key["agent-shield-monorepo"]["health"] == "failing"
    assert projects_by_key["agentpay-sdk-internal"]["module_count"] == 1
    assert projects_by_key["agentpay-sdk-internal"]["health"] == "healthy"
    assert all(project["health"] in {"healthy", "warning", "failing", "unknown"} for project in projects)
    assert all(project["module_count"] >= 0 for project in projects)
    assert all("preset" in project for project in projects)
    assert all("module_count" in project for project in projects)
    assert all("health" in project for project in projects)


def test_get_panel_project_returns_aggregated_detail() -> None:
    response = client.get("/api/v1/panel/projects/agent-shield-monorepo")

    assert response.status_code == 200
    body = response.json()
    project = body["project"]

    assert body["generated_at"].endswith("Z")
    assert project["project_key"] == "agent-shield-monorepo"
    assert project["project_name"] == "AgentShield Monorepo"
    assert project["repo_path"] == "/workspace/agent-shield-monorepo"
    assert project["preset"] == "infer-monorepo"
    assert project["onboarding_status"] == "ready"

    latest_run = project["latest_run"]
    assert latest_run["run_key"] == "agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli"
    assert latest_run["source"] == "local-cli"
    assert latest_run["git_ref"] == "main"
    assert latest_run["git_sha"] == "abc123"
    assert latest_run["triggered_by"] == "dawei"
    assert latest_run["started_at"] == "2026-03-30T10:00:00Z"
    assert latest_run["finished_at"] == "2026-03-30T10:00:31Z"
    assert latest_run["duration_sec"] == 31.0
    assert latest_run["strict_mode"] is True
    assert latest_run["status"] == "fail"
    assert latest_run["block_reason"] == "apps/web coverage below gate"

    modules = project["modules"]
    assert len(modules) == 2
    assert {module["module_name"] for module in modules} == {"apps/api", "apps/web"}

    api_module = modules[0]
    assert api_module["module_name"] == "apps/api"
    assert api_module["stack"] == "Python / FastAPI"
    assert api_module["language"] == "Python"
    assert api_module["status"] == "pass"
    assert api_module["coverage_pct"] == 81.2
    assert api_module["baseline_pct"] == 81.0
    assert api_module["coverage_gate_pct"] == 76.0
    assert api_module["coverage_delta_pct"] == 0.2
    assert api_module["coverage_parser"] == "pytest-cov-json"
    assert api_module["block_reason"] is None
    assert len(api_module["checker_results"]) == 5
    assert api_module["checker_results"][0]["checker"] == "build"
    assert api_module["checker_results"][3]["detail"] == "86 passed / 0 failed"

    web_module = modules[1]
    assert web_module["module_name"] == "apps/web"
    assert web_module["stack"] == "TypeScript / Next.js"
    assert web_module["language"] == "TypeScript"
    assert web_module["status"] == "fail"
    assert web_module["coverage_pct"] == 58.3
    assert web_module["baseline_pct"] == 72.0
    assert web_module["coverage_gate_pct"] == 67.0
    assert web_module["coverage_delta_pct"] == -13.7
    assert web_module["coverage_parser"] == "istanbul-json"
    assert web_module["block_reason"] == "coverage below gate"
    assert len(web_module["checker_results"]) == 5
    assert web_module["checker_results"][4]["checker"] == "coverage"
    assert web_module["checker_results"][4]["status"] == "fail"
    assert web_module["checker_results"][4]["detail"] == "Line 58.3%, gate >= 67.0%"


def test_get_panel_project_returns_404_for_unknown_key() -> None:
    response = client.get("/api/v1/panel/projects/unknown-project")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project 'unknown-project' not found"}


def test_get_panel_project_latest_run_returns_run_fields() -> None:
    response = client.get("/api/v1/panel/projects/agent-shield-monorepo/latest")

    assert response.status_code == 200
    body = response.json()

    assert body == {
        "generated_at": body["generated_at"],
        "project_key": "agent-shield-monorepo",
        "source": "local-cli",
        "triggered_by": "dawei",
        "status": "fail",
        "block_reason": "apps/web coverage below gate",
        "started_at": "2026-03-30T10:00:00Z",
        "finished_at": "2026-03-30T10:00:31Z",
        "duration_sec": 31.0,
    }
    assert body["generated_at"].endswith("Z")


def test_get_panel_project_latest_run_returns_404_for_unknown_key() -> None:
    response = client.get("/api/v1/panel/projects/unknown-project/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project 'unknown-project' not found"}
