"""
Mock Agent Service：聊天接口 + SQLite 存储 + APISIX 身份头兼容。
用于配合 APISIX 演示「通过 API Key 访问智能体服务」。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Mock Agent Service",
    description="模拟养成式智能体，支持 POST /chat，身份从 X-Consumer-Username 等头读取，对话落库。",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# POST /chat：主入口（便于直连或网关 path 重写为 /chat）
app.include_router(chat_router, tags=["chat"])

# POST /agent/chat：与当前 APISIX 路由 /agent/chat 一致，同一逻辑
app.include_router(chat_router, prefix="/agent", tags=["agent"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-agent-service"}
