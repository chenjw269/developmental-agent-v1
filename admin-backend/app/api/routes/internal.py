"""Internal API for mock-agent-service: token deduction (protected by INTERNAL_SECRET)."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.config import get_settings
from app.services.credential import CredentialService

router = APIRouter()
_settings = get_settings()


def _require_internal_secret(
    x_internal_secret: Annotated[Optional[str], Header(alias="X-Internal-Secret")] = None,
) -> None:
    if _settings.INTERNAL_SECRET and x_internal_secret != _settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Internal secret required")


class DeductTokenRequest(BaseModel):
    consumer_name: str


class DeductTokenResponse(BaseModel):
    remaining_tokens: int


@router.post("/deduct-token", response_model=DeductTokenResponse)
def deduct_token(
    body: DeductTokenRequest,
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(_require_internal_secret)],
):
    """
    Internal: atomically deduct 1 token for the given consumer_name.
    Returns 200 with remaining_tokens, or 402 if balance <= 0.
    """
    svc = CredentialService(db)
    success, remaining = svc.deduct_token(body.consumer_name)
    if not success:
        raise HTTPException(
            status_code=402,
            detail="Token balance exhausted or consumer not found. Please contact admin to top up.",
        )
    return DeductTokenResponse(remaining_tokens=remaining)
