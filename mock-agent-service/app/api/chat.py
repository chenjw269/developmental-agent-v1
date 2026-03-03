"""POST /chat：接收 message，从请求头取身份，先扣减 token 再落库并返回模拟回复."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import ChatService, get_consumer_from_headers
from app.services.token_client import deduct_token

router = APIRouter()


def _handle_chat(request: Request, body: ChatRequest, db: Session) -> ChatResponse:
    consumer = get_consumer_from_headers(request.headers)
    message = (body.message or "").strip() or "（无内容）"
    success, remaining = deduct_token(consumer)
    if not success:
        raise HTTPException(
            status_code=402,
            detail="Token balance exhausted or consumer not found. Please contact admin to top up.",
        )
    svc = ChatService(db)
    reply, stored = svc.chat(message=message, consumer_name=consumer)
    return ChatResponse(reply=reply, consumer=consumer, stored=stored, remaining_tokens=remaining)


@router.post("/chat", response_model=ChatResponse)
def post_chat(
    request: Request,
    body: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    """
    聊天接口：请求体 { "message": "你好" }。
    先扣减 1 token，身份从请求头读取（X-Consumer-Username 等），对话会写入 SQLite。
    """
    return _handle_chat(request, body, db)


@router.get("/chat")
def get_chat():
    """GET 仅返回使用说明，便于健康检查或文档."""
    return {
        "service": "mock-agent-service",
        "usage": "POST /chat or POST /agent/chat with JSON body: {\"message\": \"你好\"}",
        "headers": "Identity from X-Consumer-Username (APISIX) or fallback to anonymous",
    }
