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
