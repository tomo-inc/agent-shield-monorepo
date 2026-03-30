from fastapi import APIRouter, HTTPException

from app.panel.schemas.query_response_schema import (
    PanelProjectDetailResponse,
    PanelProjectLatestRunResponse,
)
from app.panel.services.project_overview_query_service import (
    get_project_detail,
    get_project_latest_run,
)

router = APIRouter()


@router.get(
    "/api/v1/panel/projects/{project_key}",
    response_model=PanelProjectDetailResponse,
    tags=["panel"],
    summary="Get panel project detail",
    operation_id="getPanelProject",
    response_description="Panel project detail record",
)
def get_panel_project(project_key: str) -> PanelProjectDetailResponse:
    project = get_project_detail(project_key)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_key}' not found")

    return project


@router.get(
    "/api/v1/panel/projects/{project_key}/latest",
    response_model=PanelProjectLatestRunResponse,
    tags=["panel"],
    summary="Get latest run for a panel project",
    operation_id="getPanelProjectLatestRun",
    response_description="Latest run data for the panel project",
)
def get_panel_project_latest_run(project_key: str) -> PanelProjectLatestRunResponse:
    latest_run = get_project_latest_run(project_key)
    if latest_run is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_key}' not found")

    return latest_run
