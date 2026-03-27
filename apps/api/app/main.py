from typing import Final

from fastapi import FastAPI

from app.schemas.qa import Capability, CapabilityCatalog, HealthResponse

APP_TITLE: Final[str] = "AgentShield QA Automation API"
APP_VERSION: Final[str] = "0.1.0"

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    summary="Phase 1 scaffold for QA automation",
    description=(
        "Monorepo-aligned FastAPI service for AgentShield. "
        "Current scope is QA automation only."
    ),
)

CAPABILITIES: Final[list[Capability]] = [
    Capability(
        name="analyzer",
        description="Identify testable targets, risk hotspots, and coverage gaps.",
        status="planned",
    ),
    Capability(
        name="generator",
        description="Generate style-aligned tests using project examples and coverage signals.",
        status="planned",
    ),
    Capability(
        name="runner",
        description="Execute tests through a framework adapter layer and normalize results.",
        status="scaffolded",
    ),
    Capability(
        name="tracker",
        description="Compare current runs to baseline snapshots and classify regressions.",
        status="planned",
    ),
]


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
    operation_id="healthz",
    response_description="Service health payload",
)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok", service="api", active_focus="qa-automation")


@app.get(
    "/api/v1/capabilities",
    response_model=CapabilityCatalog,
    tags=["system"],
    summary="List current phase capabilities",
    operation_id="listCapabilities",
    response_description="Current phase capability catalog",
)
def list_capabilities() -> CapabilityCatalog:
    return CapabilityCatalog(
        product="AgentShield",
        current_phase="phase-1-qa-automation",
        required_files=["AGENTS.md", "CLAUDE.md", "skillscloud.md"],
        capabilities=CAPABILITIES,
    )
