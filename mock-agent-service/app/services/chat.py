"""聊天业务逻辑：生成回复、落库。便于后续替换为真实 LLM 调用."""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Conversation


# 兜底身份：请求头中无 APISIX 转发信息时使用
DEFAULT_CONSUMER = "anonymous"


def get_consumer_from_headers(headers: dict) -> str:
    """
    从请求头读取调用者身份。
    APISIX 使用 key-auth 时会将 Consumer 的 username 放在 X-Consumer-Username。
    兼容：X-Consumer-Username > X-Consumer-Id > X-API-Key（脱敏） > 兜底
    """
    # 优先使用 APISIX 注入的 Consumer 用户名
    consumer = headers.get("x-consumer-username") or headers.get("X-Consumer-Username")
    if consumer:
        return consumer.strip()
    consumer = headers.get("x-consumer-id") or headers.get("X-Consumer-Id")
    if consumer:
        return str(consumer).strip()
    # 若有 API Key 头，用简短标识（不暴露完整 key）
    api_key = headers.get("x-api-key") or headers.get("X-Api-Key")
    if api_key:
        return f"key_{(api_key[:8] + '...') if len(api_key) > 8 else api_key}"
    return DEFAULT_CONSUMER


def build_mock_reply(message: str) -> str:
    """
    生成模拟回复。后续可在此处改为调用真实 LLM。
    """
    settings = get_settings()
    msg = (message or "").strip() or "（无内容）"
    return f"{settings.MOCK_REPLY_PREFIX}{msg}"


def save_conversation(
    db: Session,
    consumer_name: str,
    message: str,
    reply: str,
    session_id: str | None = None,
) -> bool:
    """将单轮对话写入 conversations 表."""
    try:
        row = Conversation(
            consumer_name=consumer_name,
            session_id=session_id,
            message=message,
            reply=reply,
        )
        db.add(row)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


class ChatService:
    """封装：解析身份、生成回复、存储、返回响应."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def chat(
        self,
        message: str,
        consumer_name: str,
        session_id: str | None = None,
    ) -> tuple[str, bool]:
        """
        生成回复并落库。返回 (reply, stored)。
        """
        reply = build_mock_reply(message)
        stored = save_conversation(
            self.db,
            consumer_name=consumer_name,
            message=message,
            reply=reply,
            session_id=session_id,
        )
        return reply, stored
