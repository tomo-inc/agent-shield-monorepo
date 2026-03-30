from fastapi import APIRouter

from app.panel.schemas.query_response_schema import PanelProjectsResponse
from app.panel.services.project_overview_query_service import get_project_overview

router = APIRouter()


@router.get(
    "/api/v1/panel/projects",
    response_model=PanelProjectsResponse,
    tags=["panel"],
    summary="List supported panel projects",
    operation_id="listPanelProjects",
    response_description="Panel project overview list",
)
def list_panel_projects() -> PanelProjectsResponse:
    return get_project_overview()
