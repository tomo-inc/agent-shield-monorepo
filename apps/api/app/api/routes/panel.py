from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.panel import (
    PanelBaselineUploadRequest,
    PanelBaselineUploadResponse,
    PanelLatestRunResponse,
    PanelProjectDetailResponse,
    PanelProjectOverviewResponse,
    PanelProjectRegisterRequest,
    PanelProjectRegisterResponse,
    PanelRunUploadRequest,
    PanelRunUploadResponse,
)
from app.services.panel.baseline_upload import upload_baselines
from app.services.panel.errors import PanelServiceError, ProjectNotFoundError, RunNotFoundError
from app.services.panel.latest_run_query import get_latest_run
from app.services.panel.project_detail_query import get_project_detail
from app.services.panel.project_overview_query import get_project_overview
from app.services.panel.project_register import register_project
from app.services.panel.run_upload import upload_run

router = APIRouter(prefix="/api/v1/panel", tags=["panel"])


def _raise_http_error(error: PanelServiceError) -> None:
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(error, (ProjectNotFoundError, RunNotFoundError)):
        status_code = status.HTTP_404_NOT_FOUND
    raise HTTPException(status_code=status_code, detail={"code": error.code, "message": error.message})


@router.post(
    "/projects/register",
    response_model=PanelProjectRegisterResponse,
    operation_id="registerPanelProject",
    summary="Register or update a panel project",
    response_description="Project registration result",
)
def register_panel_project(
    payload: PanelProjectRegisterRequest, session: Session = Depends(get_db)
) -> PanelProjectRegisterResponse:
    try:
        return register_project(session, payload)
    except PanelServiceError as error:
        session.rollback()
        _raise_http_error(error)


@router.post(
    "/baselines",
    response_model=PanelBaselineUploadResponse,
    operation_id="uploadPanelBaselines",
    summary="Upload panel baseline snapshots",
    response_description="Baseline upload result",
)
def upload_panel_baselines(
    payload: PanelBaselineUploadRequest, session: Session = Depends(get_db)
) -> PanelBaselineUploadResponse:
    try:
        return upload_baselines(session, payload)
    except PanelServiceError as error:
        session.rollback()
        _raise_http_error(error)


@router.post(
    "/runs",
    response_model=PanelRunUploadResponse,
    operation_id="uploadPanelRun",
    summary="Upload a panel run payload",
    response_description="Run upload result",
)
def upload_panel_run(payload: PanelRunUploadRequest, session: Session = Depends(get_db)) -> PanelRunUploadResponse:
    try:
        return upload_run(session, payload)
    except PanelServiceError as error:
        session.rollback()
        _raise_http_error(error)


@router.get(
    "/projects",
    response_model=PanelProjectOverviewResponse,
    operation_id="listPanelProjects",
    summary="List panel project overview rows",
    response_description="Project overview response",
)
def list_panel_projects(session: Session = Depends(get_db)) -> PanelProjectOverviewResponse:
    return get_project_overview(session)


@router.get(
    "/projects/{project_key}",
    response_model=PanelProjectDetailResponse,
    operation_id="getPanelProjectDetail",
    summary="Get panel project detail",
    response_description="Project detail response",
)
def get_panel_project_detail(project_key: str, session: Session = Depends(get_db)) -> PanelProjectDetailResponse:
    try:
        return get_project_detail(session, project_key)
    except PanelServiceError as error:
        session.rollback()
        _raise_http_error(error)


@router.get(
    "/projects/{project_key}/latest",
    response_model=PanelLatestRunResponse,
    operation_id="getPanelProjectLatestRun",
    summary="Get latest panel run detail",
    response_description="Latest run detail response",
)
def get_panel_project_latest_run(project_key: str, session: Session = Depends(get_db)) -> PanelLatestRunResponse:
    try:
        return get_latest_run(session, project_key)
    except PanelServiceError as error:
        session.rollback()
        _raise_http_error(error)
