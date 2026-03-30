from typing import Final

from fastapi import FastAPI

from app.api.routes.panel import router as panel_router
from app.schemas.qa import Capability, CapabilityCatalog, HealthResponse

APP_TITLE: Final[str] = "AgentShield QA Automation API"
APP_VERSION: Final[str] = "0.1.0"
ACTIVE_FOCUS: Final[str] = "qa-automation"
CURRENT_PHASE: Final[str] = "phase-1-qa-automation"
REQUIRED_FILES: Final[list[str]] = ["AGENTS.md", "CLAUDE.md", "skillscloud.md"]

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    summary="Phase 1 scaffold for QA automation",
    description="Monorepo-aligned FastAPI service for AgentShield. Current scope is QA automation only.",
)

CAPABILITIES: Final[tuple[Capability, ...]] = (
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
)

_HEALTH_RESPONSE: Final[HealthResponse] = HealthResponse(
    status="ok", service="api", active_focus=ACTIVE_FOCUS
)
_CAPABILITIES_CATALOG: Final[CapabilityCatalog] = CapabilityCatalog(
    product="AgentShield",
    current_phase=CURRENT_PHASE,
    required_files=REQUIRED_FILES,
    capabilities=list(CAPABILITIES),
)


@app.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
    operation_id="healthz",
    response_description="Service health payload",
)
def healthz() -> HealthResponse:
    return _HEALTH_RESPONSE


@app.get(
    "/api/v1/capabilities",
    response_model=CapabilityCatalog,
    tags=["system"],
    summary="List current phase capabilities",
    operation_id="listCapabilities",
    response_description="Current phase capability catalog",
)
def list_capabilities() -> CapabilityCatalog:
    return _CAPABILITIES_CATALOG


app.include_router(panel_router)
