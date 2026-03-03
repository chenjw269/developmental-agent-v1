"""Application routes."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationListResponse
from app.services.application import ApplicationService

router = APIRouter()


def _to_application_response(app) -> ApplicationResponse:
    return ApplicationResponse(
        id=app.id,
        user_id=app.user_id,
        reason=app.reason,
        status=app.status,
        created_at=app.created_at,
        reviewed_at=app.reviewed_at,
        user_username=app.user.username if app.user else None,
        user_email=app.user.email if app.user else None,
    )


@router.post("", response_model=ApplicationResponse)
def create_application(
    data: ApplicationCreate,
    db: Annotated[Session, Depends(get_db_session)],
):
    """User submits API Key application."""
    svc = ApplicationService(db)
    try:
        app = svc.create_application(data)
        app = svc.get_application(app.id)
        return _to_application_response(app)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
    status: Annotated[Optional[str], Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Admin: list all applications, optionally filter by status."""
    svc = ApplicationService(db)
    items, total = svc.list_applications(status=status, skip=skip, limit=limit)
    return ApplicationListResponse(
        items=[_to_application_response(a) for a in items],
        total=total,
    )


@router.post("/{application_id}/approve")
def approve_application(
    application_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: approve application and create API Key + APISIX Consumer."""
    svc = ApplicationService(db)
    try:
        credential = svc.approve(application_id)
        return {
            "message": "Approved",
            "application_id": application_id,
            "credential_id": credential.id,
            "api_key": credential.api_key,
            "consumer_name": credential.consumer_name,
            "quota_per_minute": credential.quota_per_minute,
            "token_balance": credential.token_balance,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{application_id}/reject")
def reject_application(
    application_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: reject application."""
    svc = ApplicationService(db)
    try:
        app = svc.reject(application_id)
        return {"message": "Rejected", "application_id": app.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: permanently delete application (if approved, removes credential and APISIX consumer)."""
    svc = ApplicationService(db)
    try:
        svc.delete_application(application_id)
        return {"message": "Deleted", "application_id": application_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
