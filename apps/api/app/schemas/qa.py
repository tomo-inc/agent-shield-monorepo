from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"] = Field(description="Health status")
    service: str = Field(description="Service name")
    active_focus: str = Field(description="Current delivery focus")


class Capability(BaseModel):
    name: str = Field(description="Capability name")
    description: str = Field(description="What the capability is responsible for")
    status: Literal["planned", "scaffolded", "in-progress", "stable"] = Field(
        description="Implementation status"
    )


class CapabilityCatalog(BaseModel):
    product: str = Field(description="Product name")
    current_phase: str = Field(description="Current roadmap phase")
    required_files: list[str] = Field(description="Project governance files")
    capabilities: list[Capability] = Field(description="Supported capabilities in this phase")
