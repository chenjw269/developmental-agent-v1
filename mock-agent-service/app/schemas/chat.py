"""聊天请求与响应模型."""
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str = ""


class ChatResponse(BaseModel):
    reply: str
    consumer: str
    stored: bool
    remaining_tokens: int | None = None
