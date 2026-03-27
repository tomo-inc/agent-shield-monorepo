from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(title="HealthResponse")

    status: str = Field(title="Status", description="Health status")
    service: str = Field(title="Service", description="Service name")
    active_focus: str = Field(title="Active Focus", description="Current delivery focus")


class Capability(BaseModel):
    model_config = ConfigDict(title="Capability")

    name: str = Field(title="Name", description="Capability name")
    description: str = Field(
        title="Description", description="What the capability is responsible for"
    )
    status: str = Field(title="Status", description="Implementation status")


class CapabilityCatalog(BaseModel):
    model_config = ConfigDict(title="CapabilityCatalog")

    product: str = Field(title="Product", description="Product name")
    current_phase: str = Field(title="Current Phase", description="Current roadmap phase")
    required_files: list[str] = Field(
        title="Required Files", description="Project governance files"
    )
    capabilities: list[Capability] = Field(
        title="Capabilities", description="Supported capabilities in this phase"
    )
