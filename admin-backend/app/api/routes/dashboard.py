"""Dashboard API: users list and token stats for admin."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db_session, require_admin
from app.models import User, ApiCredential, ApiKeyApplication

router = APIRouter()


@router.get("/users")
def list_dashboard_users(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """管理员：获取拥有至少一个凭证的用户列表（用于仪表盘下拉框）。"""
    sub = (
        db.query(ApiCredential.user_id)
        .filter(ApiCredential.is_active == True)
        .distinct()
        .subquery()
    )
    users = (
        db.query(User.id, User.username, User.email)
        .join(sub, User.id == sub.c.user_id)
        .order_by(User.id)
        .all()
    )
    return {
        "items": [
            {"id": u.id, "username": u.username, "email": u.email}
            for u in users
        ],
    }


@router.get("/stats")
def get_dashboard_stats(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
    user_id: Annotated[Optional[int], Query(description="用户 ID，不传则返回全平台汇总")] = None,
):
    """管理员：获取 Token 统计。按 user_id 时返回该用户汇总；不传则返回全平台汇总。"""
    q = db.query(
        func.coalesce(func.sum(ApiCredential.token_balance), 0).label("remaining"),
        func.coalesce(func.sum(ApiCredential.tokens_used), 0).label("used"),
    ).filter(ApiCredential.is_active == True)
    if user_id is not None:
        q = q.filter(ApiCredential.user_id == user_id)
    row = q.one()
    remaining = int(row.remaining)
    used = int(row.used)
    total = remaining + used
    return {
        "total_tokens": total,
        "used_tokens": used,
        "remaining_tokens": remaining,
        "user_id": user_id,
    }


@router.get("/summary")
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db_session)],
    _: Annotated[None, Depends(require_admin)],
):
    """管理员：仪表盘总览（申请数、凭证数、全平台 Token）。"""
    app_counts = (
        db.query(ApiKeyApplication.status, func.count(ApiKeyApplication.id))
        .group_by(ApiKeyApplication.status)
        .all()
    )
    by_status = {s: c for s, c in app_counts}
    cred_total = db.query(func.count(ApiCredential.id)).filter(ApiCredential.is_active == True).scalar() or 0
    token_row = (
        db.query(
            func.coalesce(func.sum(ApiCredential.token_balance), 0),
            func.coalesce(func.sum(ApiCredential.tokens_used), 0),
        )
        .filter(ApiCredential.is_active == True)
        .one()
    )
    remaining = int(token_row[0])
    used = int(token_row[1])
    return {
        "applications": {
            "pending": by_status.get("pending", 0),
            "approved": by_status.get("approved", 0),
            "rejected": by_status.get("rejected", 0),
            "total": sum(by_status.values()),
        },
        "credentials": {"active": cred_total},
        "tokens": {
            "total": remaining + used,
            "used": used,
            "remaining": remaining,
        },
    }
