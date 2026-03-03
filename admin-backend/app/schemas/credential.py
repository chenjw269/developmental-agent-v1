"""Credential schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class CredentialResponse(BaseModel):
    id: int
    user_id: int
    application_id: Optional[int] = None
    consumer_name: str
    api_key: str  # Only returned once on create; list endpoints may mask
    quota_per_minute: int
    token_balance: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CredentialListResponse(BaseModel):
    items: list[CredentialResponse]
    total: int


class CredentialQuotaUpdate(BaseModel):
    quota_per_minute: int = Field(..., ge=1, le=10000)


class CredentialBalanceUpdate(BaseModel):
    token_balance: int = Field(..., ge=0)


class SetBalanceByTarget(BaseModel):
    """设置 Token 数量：按 consumer_name（API Key 对应）或 username 二选一。"""
    consumer_name: Optional[str] = Field(None, description="API Key 对应的 consumer 名称，如 consumer_1")
    username: Optional[str] = Field(None, description="用户名字，匹配该用户下所有 credential")
    token_balance: int = Field(..., ge=0, description="要设置的 token 数量")

    @model_validator(mode="after")
    def exactly_one_target(self):
        has_consumer = self.consumer_name and str(self.consumer_name).strip()
        has_username = self.username and str(self.username).strip()
        if has_consumer == has_username:
            raise ValueError("必须且只能填写 consumer_name 或 username 其一")
        return self
