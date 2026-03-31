from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.models import Base
from app.main import app


client = TestClient(app)


def _make_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _make_db_override(factory: sessionmaker[Session]):
    def _override_get_db() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    return _override_get_db


def _seed_panel_data() -> TestClient:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    panel_client = TestClient(app)

    first_project_payload = {
        "project_key": "agent-shield-monorepo",
        "project_name": "AgentShield Monorepo",
        "repo_path": "/workspace/agent-shield-monorepo",
        "preset": "infer-monorepo",
        "onboarding_status": "ready",
        "modules": [
            {"module_name": "apps/api", "stack": "Python / FastAPI", "language": "Python"},
            {"module_name": "apps/web", "stack": "TypeScript / Next.js", "language": "TypeScript"},
        ],
    }
    second_project_payload = {
        "project_key": "agentpay-sdk-internal",
        "project_name": "AgentPay SDK Internal",
        "repo_path": "/workspace/agentpay-sdk-internal",
        "preset": "agentpay-sdk",
        "onboarding_status": "ready",
        "modules": [{"module_name": "sdk/python", "stack": "Python", "language": "Python"}],
    }
    baseline_payload = {
        "project_key": "agent-shield-monorepo",
        "updated_at": "2026-03-30T10:00:00Z",
        "modules": [
            {"module_name": "apps/api", "baseline_pct": 81.0},
            {"module_name": "apps/web", "baseline_pct": 72.0},
        ],
    }
    run_payload = {
        "project_key": "agent-shield-monorepo",
        "run_key": "agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
        "source": "local-cli",
        "git_ref": "main",
        "git_sha": "abc123",
        "triggered_by": "dawei",
        "started_at": "2026-03-30T10:00:00Z",
        "finished_at": "2026-03-30T10:00:31Z",
        "duration_sec": 31.0,
        "strict_mode": True,
        "status": "fail",
        "block_reason": "apps/web coverage below gate",
        "modules": [
            {
                "module_name": "apps/api",
                "stack": "Python / FastAPI",
                "language": "Python",
                "status": "pass",
                "coverage_pct": 81.2,
                "baseline_pct": 81.0,
                "coverage_gate_pct": 76.0,
                "coverage_delta_pct": 0.2,
                "coverage_parser": "pytest-cov-json",
                "block_reason": None,
                "checker_results": [
                    {"checker": "build", "status": "pass", "detail": "", "duration_sec": 3.2},
                    {"checker": "lint", "status": "pass", "detail": "", "duration_sec": 1.1},
                    {"checker": "typecheck", "status": "pass", "detail": "", "duration_sec": 1.4},
                    {"checker": "test", "status": "pass", "detail": "86 passed / 0 failed", "duration_sec": 6.7},
                    {"checker": "coverage", "status": "pass", "detail": "Line 81.2%, gate >= 76.0%", "duration_sec": 1.0},
                ],
            },
            {
                "module_name": "apps/web",
                "stack": "TypeScript / Next.js",
                "language": "TypeScript",
                "status": "fail",
                "coverage_pct": 58.3,
                "baseline_pct": 72.0,
                "coverage_gate_pct": 67.0,
                "coverage_delta_pct": -13.7,
                "coverage_parser": "istanbul-json",
                "block_reason": "coverage below gate",
                "checker_results": [
                    {"checker": "build", "status": "pass", "detail": "", "duration_sec": 12.3},
                    {"checker": "lint", "status": "pass", "detail": "", "duration_sec": 1.7},
                    {"checker": "typecheck", "status": "pass", "detail": "", "duration_sec": 1.5},
                    {"checker": "test", "status": "pass", "detail": "41 passed / 0 failed", "duration_sec": 4.8},
                    {"checker": "coverage", "status": "fail", "detail": "Line 58.3%, gate >= 67.0%", "duration_sec": 1.3},
                ],
            },
        ],
    }

    assert panel_client.post("/api/v1/panel/projects/register", json=first_project_payload).status_code == 200
    assert panel_client.post("/api/v1/panel/projects/register", json=second_project_payload).status_code == 200
    assert panel_client.post("/api/v1/panel/baselines", json=baseline_payload).status_code == 200
    assert panel_client.post("/api/v1/panel/runs", json=run_payload).status_code == 200

    return panel_client


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
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()

    assert body["generated_at"].endswith("Z")
    assert len(body["projects"]) == 2


def test_list_panel_projects_exposes_mock_project_fields() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    projects = response.json()["projects"]
    projects_by_key = {project["project_key"]: project for project in projects}

    assert projects_by_key["agent-shield-monorepo"] == {
        "project_key": "agent-shield-monorepo",
        "project_name": "AgentShield Monorepo",
        "preset": "infer-monorepo",
        "module_count": 2,
        "onboarding_status": "ready",
        "health": "failing",
        "check_all": "fail",
        "last_run_at": "2026-03-30T10:00:31",
        "block_reason": "apps/web coverage below gate",
        "coverage_avg_pct": 69.75,
    }
    assert projects_by_key["agentpay-sdk-internal"] == {
        "project_key": "agentpay-sdk-internal",
        "project_name": "AgentPay SDK Internal",
        "preset": "agentpay-sdk",
        "module_count": 1,
        "onboarding_status": "ready",
        "health": "unknown",
        "check_all": "not-run",
        "last_run_at": None,
        "block_reason": None,
        "coverage_avg_pct": None,
    }


def test_list_panel_projects_derives_module_count_and_health() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    projects = response.json()["projects"]
    projects_by_key = {project["project_key"]: project for project in projects}

    assert projects_by_key["agent-shield-monorepo"]["module_count"] == 2
    assert projects_by_key["agent-shield-monorepo"]["health"] == "failing"
    assert projects_by_key["agent-shield-monorepo"]["check_all"] == "fail"
    assert projects_by_key["agentpay-sdk-internal"]["module_count"] == 1
    assert projects_by_key["agentpay-sdk-internal"]["health"] == "unknown"
    assert projects_by_key["agentpay-sdk-internal"]["check_all"] == "not-run"
    assert all(project["health"] in {"healthy", "warning", "failing", "unknown"} for project in projects)
    assert all(project["module_count"] >= 0 for project in projects)
    assert all("preset" in project for project in projects)
    assert all("module_count" in project for project in projects)
    assert all("health" in project for project in projects)


def test_get_panel_project_returns_aggregated_detail() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects/agent-shield-monorepo")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    project = body["project"]

    assert body["generated_at"].endswith("Z")
    assert project["project_key"] == "agent-shield-monorepo"
    assert project["project_name"] == "AgentShield Monorepo"
    assert project["preset"] == "infer-monorepo"
    assert project["onboarding_status"] == "ready"

    latest_run = project["latest_run"]
    assert latest_run["run_key"] == "agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli"
    assert latest_run["finished_at"] == "2026-03-30T10:00:31"
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
    coverage_result = next(
        result for result in web_module["checker_results"] if result["checker"] == "coverage"
    )
    assert coverage_result["status"] == "fail"
    assert coverage_result["detail"] == "Line 58.3%, gate >= 67.0%"


def test_get_panel_project_returns_404_for_unknown_key() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects/unknown-project")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_get_panel_project_latest_run_returns_run_fields() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects/agent-shield-monorepo/latest")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    run = body["run"]

    assert run == {
        "run_key": "agent-shield-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
        "source": "local-cli",
        "git_ref": "main",
        "git_sha": "abc123",
        "triggered_by": "dawei",
        "started_at": "2026-03-30T10:00:00",
        "finished_at": "2026-03-30T10:00:31",
        "duration_sec": 31.0,
        "strict_mode": True,
        "status": "fail",
        "block_reason": "apps/web coverage below gate",
        "modules": run["modules"],
    }
    assert body["generated_at"].endswith("Z")
    assert len(run["modules"]) == 2


def test_get_panel_project_latest_run_returns_404_for_unknown_key() -> None:
    panel_client = _seed_panel_data()
    response = panel_client.get("/api/v1/panel/projects/unknown-project/latest")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"
