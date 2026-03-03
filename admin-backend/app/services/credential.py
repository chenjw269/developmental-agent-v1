"""Credential and APISIX consumer lifecycle."""
import secrets
from typing import Optional, Tuple

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ApiCredential, ApiKeyApplication, User
from app.services.apisix import ApisixClient, ApisixError

_settings = get_settings()


def _generate_api_key() -> str:
    """Generate a random API key (e.g. for header)."""
    return f"apisix_{secrets.token_urlsafe(24)}"


def _consumer_name(application_id: int) -> str:
    """Unique consumer name for APISIX."""
    return f"consumer_{application_id}"


class CredentialService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.apisix = ApisixClient()

    def create_for_application(self, application: ApiKeyApplication) -> ApiCredential:
        """Create a new credential for an approved application (called from approve)."""
        api_key = _generate_api_key()
        consumer_name = _consumer_name(application.id)
        cred = ApiCredential(
            user_id=application.user_id,
            application_id=application.id,
            consumer_name=consumer_name,
            api_key=api_key,
            quota_per_minute=60,
            token_balance=_settings.INITIAL_TOKEN_BALANCE,
            is_active=True,
        )
        self.db.add(cred)
        self.db.flush()
        return cred

    def list_credentials(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> tuple[list[ApiCredential], int]:
        q = self.db.query(ApiCredential)
        if active_only:
            q = q.filter(ApiCredential.is_active == True)
        total = q.count()
        items = q.order_by(ApiCredential.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_credential(self, credential_id: int) -> Optional[ApiCredential]:
        return self.db.query(ApiCredential).filter(ApiCredential.id == credential_id).first()

    def get_credential_by_consumer_name(self, consumer_name: str) -> Optional[ApiCredential]:
        return (
            self.db.query(ApiCredential)
            .filter(ApiCredential.consumer_name == consumer_name, ApiCredential.is_active == True)
            .first()
        )

    def deduct_token(self, consumer_name: str) -> Tuple[bool, int]:
        """
        Atomically deduct 1 token for the consumer. Returns (success, remaining_tokens).
        If balance <= 0, no deduction, returns (False, 0).
        """
        cred = self.get_credential_by_consumer_name(consumer_name)
        if not cred or cred.token_balance <= 0:
            return False, 0
        # Atomic: deduct 1 from balance and increment tokens_used
        stmt = (
            update(ApiCredential)
            .where(ApiCredential.id == cred.id, ApiCredential.token_balance > 0)
            .values(
                token_balance=ApiCredential.token_balance - 1,
                tokens_used=ApiCredential.tokens_used + 1,
            )
        )
        result = self.db.execute(stmt)
        self.db.commit()
        if result.rowcount == 0:
            return False, 0
        cred = self.get_credential(cred.id)
        return True, cred.token_balance

    def update_balance(self, credential_id: int, token_balance: int) -> ApiCredential:
        cred = self.get_credential(credential_id)
        if not cred:
            raise ValueError("Credential not found")
        cred.token_balance = token_balance
        self.db.commit()
        self.db.refresh(cred)
        return cred

    def set_balance_by_consumer_name(self, consumer_name: str, token_balance: int) -> ApiCredential:
        """按 API Key 对应的 consumer 名称设置 token 数量。"""
        cred = self.db.query(ApiCredential).filter(ApiCredential.consumer_name == consumer_name).first()
        if not cred:
            raise ValueError(f"Consumer not found: {consumer_name}")
        cred.token_balance = token_balance
        self.db.commit()
        self.db.refresh(cred)
        return cred

    def set_balance_by_username(self, username: str, token_balance: int) -> list[ApiCredential]:
        """按用户名设置该用户下所有 credential 的 token 数量。"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError(f"User not found: {username}")
        creds = self.db.query(ApiCredential).filter(ApiCredential.user_id == user.id).all()
        if not creds:
            raise ValueError(f"No credentials for user: {username}")
        for c in creds:
            c.token_balance = token_balance
        self.db.commit()
        for c in creds:
            self.db.refresh(c)
        return creds

    def update_quota(self, credential_id: int, quota_per_minute: int) -> ApiCredential:
        cred = self.get_credential(credential_id)
        if not cred:
            raise ValueError("Credential not found")
        cred.quota_per_minute = quota_per_minute
        try:
            self.apisix.update_consumer_quota(cred.consumer_name, quota_per_minute)
        except ApisixError as e:
            raise RuntimeError(f"Failed to update APISIX quota: {e.message}") from e
        self.db.commit()
        self.db.refresh(cred)
        return cred

    def disable(self, credential_id: int) -> ApiCredential:
        cred = self.get_credential(credential_id)
        if not cred:
            raise ValueError("Credential not found")
        try:
            self.apisix.delete_consumer(cred.consumer_name)
        except ApisixError as e:
            if e.status_code != 404:
                raise RuntimeError(f"Failed to disable in APISIX: {e.message}") from e
        cred.is_active = False
        self.db.commit()
        self.db.refresh(cred)
        return cred

    def enable(self, credential_id: int) -> ApiCredential:
        cred = self.get_credential(credential_id)
        if not cred:
            raise ValueError("Credential not found")
        if cred.is_active:
            return cred
        try:
            self.apisix.create_consumer(
                username=cred.consumer_name,
                api_key_value=cred.api_key,
                quota_per_minute=cred.quota_per_minute,
            )
        except ApisixError as e:
            raise RuntimeError(f"Failed to create APISIX consumer: {e.message}") from e
        cred.is_active = True
        self.db.commit()
        self.db.refresh(cred)
        return cred

    def delete(self, credential_id: int) -> None:
        """Permanently delete credential and remove from APISIX."""
        cred = self.get_credential(credential_id)
        if not cred:
            raise ValueError("Credential not found")
        try:
            self.apisix.delete_consumer(cred.consumer_name)
        except ApisixError as e:
            if e.status_code != 404:
                raise RuntimeError(f"Failed to delete APISIX consumer: {e.message}") from e
        self.db.delete(cred)
        self.db.commit()
