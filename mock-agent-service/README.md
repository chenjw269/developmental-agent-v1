# Mock Agent Service

FastAPI 模拟智能体服务：提供 `POST /chat`（及 `POST /agent/chat`），从请求头读取调用者身份，对话落库 SQLite，返回模拟回复。用于配合 APISIX 演示「通过 API Key 访问智能体」。

## 目录结构

```
mock-agent-service/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 入口，挂载 /chat 与 /agent/chat
│   ├── config.py         # DATABASE_URL、MOCK_REPLY_PREFIX
│   ├── database.py       # 引擎、Session、get_db、init_db
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py   # conversations 表
│   │   └── session.py        # sessions 表（可选）
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat.py       # ChatRequest, ChatResponse
│   ├── api/
│   │   ├── __init__.py
│   │   └── chat.py       # POST /chat 实现
│   └── services/
│       ├── __init__.py
│       └── chat.py        # 身份解析、生成回复、落库
├── requirements.txt
├── Dockerfile
└── README.md
```

## 接口

- **POST /chat** 或 **POST /agent/chat**
  - 请求体：`{ "message": "你好" }`
  - 身份：从请求头读取（见下），未命中时使用 `anonymous`
  - 响应示例：`{ "reply": "我是养成式智能体，很高兴和你交流：你好", "consumer": "user_001", "stored": true }`

## 身份头（APISIX 兼容）

按优先级读取：

1. `X-Consumer-Username`（APISIX key-auth 常用）
2. `X-Consumer-Id`
3. `X-Api-Key`（脱敏展示为 `key_xxxx...`）
4. 兜底：`anonymous`

若 APISIX 需将 Consumer 名传给上游，可在路由上配置 `proxy-rewrite` 或使用支持设置上游头的插件，将 `consumer_name` 写入 `X-Consumer-Username`。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `DATABASE_URL` | `sqlite:///./agent.db` | 数据库连接 |
| `MOCK_REPLY_PREFIX` | `我是养成式智能体，很高兴和你交流：` | 模拟回复前缀，便于后续替换为真实 LLM |

## 启动方式

```bash
cd mock-agent-service
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或 Docker：

```bash
docker build -t mock-agent-service .
docker run -p 8000:8000 mock-agent-service
```

- 本地：http://localhost:8000/docs  
- 健康检查：http://localhost:8000/health  

## 数据库表

- **conversations**：id, consumer_name, session_id, message, reply, created_at  
- **sessions**（可选）：id, consumer_name, session_id, created_at  

首次启动时 `init_db()` 会自动建表。
