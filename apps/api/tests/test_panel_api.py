from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.models import Base
from app.main import app


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


def test_panel_project_register_and_overview_are_idempotent() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    payload = {
        "project_key": "infer-monorepo",
        "project_name": "infer-monorepo",
        "repo_path": ".",
        "preset": None,
        "onboarding_status": "ready",
        "modules": [
            {"module_name": "apps/api", "stack": "Python / FastAPI", "language": "Python"},
            {"module_name": "apps/web", "stack": "TypeScript / Next.js", "language": "TypeScript"},
        ],
    }

    first = client.post("/api/v1/panel/projects/register", json=payload)
    second = client.post("/api/v1/panel/projects/register", json=payload)
    overview = client.get("/api/v1/panel/projects")

    app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["project_id"] == second.json()["project_id"]
    assert overview.status_code == 200
    body = overview.json()
    assert len(body["projects"]) == 1
    assert body["projects"][0]["module_count"] == 2
    assert body["projects"][0]["check_all"] == "not-run"
    assert body["projects"][0]["health"] == "unknown"
    assert body["projects"][0]["coverage_avg_pct"] is None


def test_panel_run_upload_and_read_queries() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    register_payload = {
        "project_key": "infer-monorepo",
        "project_name": "infer-monorepo",
        "repo_path": ".",
        "preset": None,
        "onboarding_status": "ready",
        "modules": [
            {"module_name": "apps/api", "stack": "Python / FastAPI", "language": "Python"},
            {"module_name": "apps/web", "stack": "TypeScript / Next.js", "language": "TypeScript"},
        ],
    }
    baseline_payload = {
        "project_key": "infer-monorepo",
        "updated_at": "2026-03-30T10:00:00Z",
        "modules": [
            {"module_name": "apps/api", "baseline_pct": 81.0},
            {"module_name": "apps/web", "baseline_pct": 72.0},
        ],
    }
    run_payload = {
        "project_key": "infer-monorepo",
        "run_key": "infer-monorepo_abc123_2026-03-30T10:00:00Z_local-cli",
        "source": "local-cli",
        "git_ref": "main",
        "git_sha": "abc123",
        "triggered_by": "alice",
        "started_at": "2026-03-30T10:00:00Z",
        "finished_at": "2026-03-30T10:00:31Z",
        "duration_sec": 31.2,
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
                    {"checker": "coverage", "status": "pass", "detail": "Line 81.2%", "duration_sec": 1.0},
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
                    {"checker": "coverage", "status": "fail", "detail": "Line 58.3%", "duration_sec": 1.3},
                ],
            },
        ],
    }

    assert client.post("/api/v1/panel/projects/register", json=register_payload).status_code == 200
    assert client.post("/api/v1/panel/baselines", json=baseline_payload).status_code == 200

    upload_response = client.post("/api/v1/panel/runs", json=run_payload)
    overview_response = client.get("/api/v1/panel/projects")
    latest_response = client.get("/api/v1/panel/projects/infer-monorepo/latest")
    detail_response = client.get("/api/v1/panel/projects/infer-monorepo")

    app.dependency_overrides.clear()

    assert upload_response.status_code == 200
    assert upload_response.json()["checker_results_upserted"] == 4

    assert overview_response.status_code == 200
    overview_body = overview_response.json()
    assert overview_body["projects"][0]["coverage_avg_pct"] == 69.75

    assert latest_response.status_code == 200
    latest_body = latest_response.json()
    assert latest_body["run"]["status"] == "fail"
    assert len(latest_body["run"]["modules"]) == 2
    assert latest_body["run"]["modules"][1]["baseline_pct"] == 72.0

    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["project"]["latest_run"]["run_key"] == run_payload["run_key"]
    assert detail_body["project"]["modules"][0]["checker_results"]


def test_panel_latest_run_requires_existing_run() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    register_payload = {
        "project_key": "infer-monorepo",
        "project_name": "infer-monorepo",
        "repo_path": ".",
        "preset": None,
        "onboarding_status": "ready",
        "modules": [{"module_name": "apps/api", "stack": "Python / FastAPI", "language": "Python"}],
    }
    assert client.post("/api/v1/panel/projects/register", json=register_payload).status_code == 200

    response = client.get("/api/v1/panel/projects/infer-monorepo/latest")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "RUN_NOT_FOUND"


def test_panel_baseline_upload_requires_existing_project() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    payload = {
        "project_key": "missing-project",
        "updated_at": "2026-03-30T10:00:00Z",
        "modules": [{"module_name": "apps/api", "baseline_pct": 81.0}],
    }

    response = client.post("/api/v1/panel/baselines", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_panel_run_upload_requires_existing_project() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    payload = {
        "project_key": "missing-project",
        "run_key": "run-1",
        "strict_mode": False,
        "status": "pass",
        "modules": [],
    }

    response = client.post("/api/v1/panel/runs", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_panel_project_detail_requires_existing_project() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    response = client.get("/api/v1/panel/projects/missing-project")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_panel_project_detail_returns_empty_latest_run_when_project_has_no_runs() -> None:
    session_factory = _make_test_session_factory()
    app.dependency_overrides[get_db] = _make_db_override(session_factory)
    client = TestClient(app)

    register_payload = {
        "project_key": "infer-monorepo",
        "project_name": "infer-monorepo",
        "repo_path": ".",
        "preset": None,
        "onboarding_status": "pending",
        "modules": [{"module_name": "apps/api", "stack": None, "language": None}],
    }
    assert client.post("/api/v1/panel/projects/register", json=register_payload).status_code == 200

    response = client.get("/api/v1/panel/projects/infer-monorepo")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["project"]["latest_run"] is None
    assert body["project"]["modules"] == []
