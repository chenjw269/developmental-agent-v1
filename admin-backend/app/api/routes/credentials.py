"""Credential routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.schemas.credential import (
    CredentialResponse,
    CredentialListResponse,
    CredentialQuotaUpdate,
    CredentialBalanceUpdate,
    SetBalanceByTarget,
)
from app.services.credential import CredentialService

router = APIRouter()


def _to_credential_response(c, mask_key: bool = False) -> CredentialResponse:
    key = c.api_key
    if mask_key and len(key) > 8:
        key = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
    return CredentialResponse(
        id=c.id,
        user_id=c.user_id,
        application_id=c.application_id,
        consumer_name=c.consumer_name,
        api_key=key,
        quota_per_minute=c.quota_per_minute,
        token_balance=getattr(c, "token_balance", 0),
        is_active=c.is_active,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=CredentialListResponse)
def list_credentials(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    active_only: Annotated[bool, Query()] = False,
):
    """Admin: list all credentials."""
    svc = CredentialService(db)
    items, total = svc.list_credentials(skip=skip, limit=limit, active_only=active_only)
    return CredentialListResponse(
        items=[_to_credential_response(c, mask_key=True) for c in items],
        total=total,
    )


@router.post("/set-balance")
def set_balance_by_target(
    data: SetBalanceByTarget,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: 按 consumer_name（API Key）或 username 设置 token 数量。"""
    svc = CredentialService(db)
    try:
        if data.consumer_name:
            cred = svc.set_balance_by_consumer_name(
                data.consumer_name.strip(), data.token_balance
            )
            return {
                "message": "Token 数量已更新",
                "target": "consumer_name",
                "value": data.consumer_name,
                "token_balance": data.token_balance,
                "updated": [_to_credential_response(cred, mask_key=True)],
            }
        else:
            creds = svc.set_balance_by_username(
                (data.username or "").strip(), data.token_balance
            )
            return {
                "message": "Token 数量已更新",
                "target": "username",
                "value": (data.username or "").strip(),
                "token_balance": data.token_balance,
                "updated": [_to_credential_response(c, mask_key=True) for c in creds],
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{credential_id}/balance", response_model=CredentialResponse)
def update_balance(
    credential_id: int,
    data: CredentialBalanceUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: update token_balance for a credential."""
    svc = CredentialService(db)
    try:
        cred = svc.update_balance(credential_id, data.token_balance)
        return _to_credential_response(cred, mask_key=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{credential_id}/quota", response_model=CredentialResponse)
def update_quota(
    credential_id: int,
    data: CredentialQuotaUpdate,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: update quota per minute for a credential."""
    svc = CredentialService(db)
    try:
        cred = svc.update_quota(credential_id, data.quota_per_minute)
        return _to_credential_response(cred, mask_key=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.patch("/{credential_id}/disable", response_model=CredentialResponse)
def disable_credential(
    credential_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: disable API Key (remove from APISIX)."""
    svc = CredentialService(db)
    try:
        cred = svc.disable(credential_id)
        return _to_credential_response(cred, mask_key=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.patch("/{credential_id}/enable", response_model=CredentialResponse)
def enable_credential(
    credential_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: re-enable API Key (recreate APISIX consumer)."""
    svc = CredentialService(db)
    try:
        cred = svc.enable(credential_id)
        return _to_credential_response(cred, mask_key=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{credential_id}")
def delete_credential(
    credential_id: int,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """Admin: permanently delete API Key (remove from APISIX and DB)."""
    svc = CredentialService(db)
    try:
        svc.delete(credential_id)
        return {"message": "Deleted", "credential_id": credential_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
