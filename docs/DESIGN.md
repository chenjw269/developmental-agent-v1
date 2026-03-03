# 基于 Apache APISIX 的智能体 API 网关演示系统 — 设计文档

## 1. 项目目录结构

```
developmental-agent-v0/
├── docker-compose.yml          # 编排：etcd、APISIX、admin-backend、agent-service、frontend(可选)
├── .env.example                # 环境变量示例
├── README.md
│
├── docs/
│   └── DESIGN.md               # 本设计文档
│
├── infra/                      # 基础设施与网关配置
│   ├── apisix/
│   │   ├── config.yaml         # APISIX 节点配置（指向 etcd）
│   │   └── README.md           # APISIX 配置说明与同步逻辑
│   └── etcd/                   # 如需持久化可挂载卷
│
├── admin-backend/              # 管理后端（FastAPI + SQLAlchemy）
│   ├── Dockerfile
│   ├── pyproject.toml          # 或 requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置（DB、APISIX Admin API 等）
│   │   ├── database.py        # 引擎、Session、依赖
│   │   ├── models/             # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── api_key_application.py
│   │   │   ├── api_key.py
│   │   │   └── quota.py
│   │   ├── schemas/            # Pydantic 请求/响应
│   │   │   ├── __init__.py
│   │   │   ├── application.py
│   │   │   ├── api_key.py
│   │   │   └── quota.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py         # 公共依赖（如 get_db）
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── applications.py   # 用户：申请 API Key
│   │   │   │   ├── keys.py           # 用户：我的 Key / 测试调用
│   │   │   │   ├── admin_applications.py  # 管理员：审批
│   │   │   │   ├── admin_keys.py     # 管理员：发放 Key、查列表
│   │   │   │   └── admin_quota.py    # 管理员：修改配额
│   │   │   └── router.py
│   │   ├── services/           # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── application.py  # 申请创建、状态流转
│   │   │   ├── api_key.py      # 发放 Key、同步 APISIX Consumer
│   │   │   └── quota.py        # 配额读写、同步 APISIX limit-count
│   │   └── integrations/
│   │       ├── __init__.py
│   │       └── apisix.py       # 调用 APISIX Admin API（Consumer/Route/Plugin）
│   ├── migrations/             # Alembic 迁移（可选，演示可用 create_all）
│   └── tests/
│
├── agent-service/              # 模拟智能体服务（FastAPI）
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py         # SQLite，仅本服务用
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── conversation.py
│   │   ├── schemas/
│   │   │   └── chat.py
│   │   ├── api/
│   │   │   └── chat.py         # POST /chat 等
│   │   └── services/
│   │       └── chat.py         # 对话存储与简单回复逻辑
│   └── tests/
│
└── frontend/                   # React + Vite + TypeScript
    ├── Dockerfile              # 多阶段：build + nginx 或 serve
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    ├── public/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/                # 封装对 admin-backend 与网关的请求
    │   │   ├── client.ts
    │   │   ├── applications.ts
    │   │   ├── keys.ts
    │   │   └── admin.ts
    │   ├── pages/
    │   │   ├── UserApply.tsx       # 用户：申请 API Key
    │   │   ├── UserKeys.tsx        # 用户：我的 Key、测试调用
    │   │   ├── AdminApplications.tsx  # 管理员：审批列表与操作
    │   │   ├── AdminKeys.tsx       # 管理员：Key 列表、发放
    │   │   └── AdminQuota.tsx      # 管理员：修改配额
    │   ├── components/
    │   │   ├── Layout.tsx
    │   │   └── ...
    │   ├── routes.tsx
    │   └── types/
    │       └── index.ts
    └── tests/
```

---

## 2. 系统架构说明

### 2.1 整体架构图（逻辑）

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                      浏览器 (Frontend)                    │
                    └───────────────┬─────────────────────┬───────────────────┘
                                    │                     │
         用户/管理员                 │ 申请/审批/配额       │ 调用智能体（带 API Key）
         访问管理功能                ▼                     ▼
                    ┌───────────────────────┐   ┌─────────────────────────────┐
                    │   Admin Backend       │   │   Apache APISIX (Gateway)   │
                    │   (FastAPI)           │   │   - Key Auth                │
                    │   - 申请/审批/Key/配额 │   │   - Limit Count (配额)      │
                    └───────────┬───────────┘   └──────────────┬──────────────┘
                                │                             │
                                │ 同步 Consumer/Plugin        │ 转发已鉴权请求
                                │ (Admin API)                 ▼
                                │                 ┌─────────────────────────────┐
                    ┌───────────▼───────────┐     │   Agent Service (FastAPI)   │
                    │   etcd                │     │   - POST /chat               │
                    │   (APISIX 配置存储)   │     │   - 对话存储 / 模拟回复      │
                    └──────────────────────┘     └─────────────────────────────┘
```

### 2.2 数据流简述

| 场景 | 路径 | 说明 |
|------|------|------|
| 用户申请 API Key | 浏览器 → Admin Backend | 提交申请，写入 DB，状态 pending |
| 管理员审批 | 浏览器 → Admin Backend | 审批通过后创建 API Key、Consumer（APISIX）、绑定 limit-count |
| 管理员改配额 | 浏览器 → Admin Backend | 更新 DB 并调用 APISIX 更新 limit-count 插件 |
| 用户调用智能体 | 浏览器 → APISIX → Agent Service | 请求头带 `X-API-Key`，网关鉴权+限流后转发 |
| 对话存储 | APISIX → Agent Service | 仅智能体服务读写 SQLite 对话表 |

### 2.3 关键约束

- **不直连智能体**：前端/用户只通过网关的对外域名（如 `http://gateway:9080` 或暴露端口）访问智能体接口，不直接访问 Agent Service。
- **鉴权与配额在网关**：API Key 校验与“每分钟 N 次”由 APISIX 完成；Admin Backend 负责业务数据与同步网关配置。
- **演示用**：认证可采用“用户标识 + 管理员标识”的简单方式（如固定管理员 Token 或简单登录），不引入完整 OAuth/OIDC。

---

## 3. 各模块职责划分

| 模块 | 职责 | 不负责 |
|------|------|--------|
| **Frontend** | 用户申请、我的 Key、测试调用；管理员审批、发放 Key、改配额 | 不存 API Key 明文长期展示（可脱敏）；不直接调 Agent Service |
| **Admin Backend** | 申请 CRUD、审批流、API Key 发放与撤销、配额配置；调用 APISIX Admin API 同步 Consumer/Plugin | 不解析或校验请求中的 API Key（由网关做）；不存储对话内容 |
| **APISIX** | 路由到 Agent Service、key-auth 鉴权、limit-count 限流；配置存 etcd | 不执行业务逻辑；不持久化申请/审批数据 |
| **etcd** | 存储 APISIX 的 routes、consumers、plugins 等配置 | 不存业务库表 |
| **Agent Service** | 提供 /chat 等接口；对话落库；模拟回复 | 不鉴权、不限流；不管理 API Key 或配额 |

---

## 4. 数据库表设计

数据库仅用于 **Admin Backend** 与 **Agent Service**，两者可共用 SQLite 文件（演示）或分库。下表按“逻辑库”分列。

### 4.1 Admin Backend 库（SQLite，如 `admin.db`）

| 表名 | 说明 |
|------|------|
| **user** | 申请方/使用者（演示可简化：仅姓名、邮箱、创建时间） |
| **api_key_application** | API Key 申请单 |
| **api_key** | 已发放的 API Key（与 APISIX Consumer 一一对应） |
| **quota** | 按 Key 或用户的配额配置（供 Admin 展示与同步网关） |

**user**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| name | VARCHAR(128) | 申请人姓名 |
| email | VARCHAR(255) | 邮箱（唯一，用于关联申请） |
| created_at | DATETIME | 创建时间 |

**api_key_application**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| user_id | INTEGER FK → user.id | 申请人 |
| reason | TEXT | 申请理由（可选） |
| status | VARCHAR(20) | pending / approved / rejected |
| reviewed_at | DATETIME | 审批时间 |
| reviewed_by | VARCHAR(64) | 审批人标识（演示用） |
| created_at | DATETIME | 申请时间 |

**api_key**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| application_id | INTEGER FK → api_key_application.id | 来源申请 |
| user_id | INTEGER FK → user.id | 所属用户 |
| key_hash | VARCHAR(64) | Key 的哈希（用于校验与脱敏展示，如前 8 位） |
| key_prefix | VARCHAR(16) | 展示用前缀，如 apisix_xxx… |
| apisix_consumer_id | VARCHAR(64) | APISIX Consumer 的 id（如 username） |
| revoked_at | DATETIME NULL | 撤销时间，NULL 表示有效 |
| created_at | DATETIME | 发放时间 |

**quota**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| api_key_id | INTEGER FK → api_key.id | 关联的 Key（一对一或按 Key 聚合） |
| requests_per_minute | INTEGER | 每分钟最大请求数（固定时间窗口） |
| updated_at | DATETIME | 最后修改时间 |

说明：APISIX 的 limit-count 以 Consumer 为维度时，每个 Consumer 一个插件配置；Admin Backend 以 `api_key_id` 对应一个 Consumer，便于“管理员改配额”时只更新该 Consumer 的插件。

### 4.2 Agent Service 库（SQLite，如 `agent.db`，可与 admin 同文件演示）

| 表名 | 说明 |
|------|------|
| **conversation** | 单次会话（可选：多轮用 session_id 关联） |
| **message** | 单条消息（role + content） |

**conversation**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| session_id | VARCHAR(64) | 会话 ID（前端传入或服务端生成） |
| user_identifier | VARCHAR(64) | 来自网关的 Consumer 名或 X-User-Id，便于按用户查 |
| created_at | DATETIME | 创建时间 |

**message**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 |
| conversation_id | INTEGER FK → conversation.id | 所属会话 |
| role | VARCHAR(16) | user / assistant |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间 |

---

## 5. 后端 API 设计

以下为 **Admin Backend** 与 **Agent Service** 的 REST API 设计；网关对外路径在“APISIX 配置”中统一。

### 5.1 Admin Backend（管理后端）

基础路径：`/api/v1`。鉴权：演示可用 Header `X-Admin-Token` 区分管理员与普通用户；或简单分为“需 Admin”与“不需 Admin”两组。

**用户侧**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /applications | 提交 API Key 申请（body: name, email, reason?） |
| GET | /applications/me | 当前用户（以 email 或 session 标识）的申请列表 |
| GET | /keys | 我的 API Key 列表（脱敏：key_prefix + 状态） |
| GET | /keys/:id | 某 Key 详情（不含完整 Key，可含配额） |
| POST | /keys/:id/revoke | 撤销自己的 Key（软删，设 revoked_at） |

**管理员侧**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /admin/applications | 申请列表（支持 status 筛选） |
| GET | /admin/applications/:id | 申请详情 |
| POST | /admin/applications/:id/approve | 审批通过：创建 API Key、APISIX Consumer、默认配额 |
| POST | /admin/applications/:id/reject | 审批拒绝 |
| GET | /admin/keys | 所有 Key 列表（分页） |
| GET | /admin/keys/:id | Key 详情 |
| PUT | /admin/keys/:id/quota | 修改配额（body: requests_per_minute） |
| POST | /admin/keys/:id/revoke | 管理员撤销 Key |

**通用**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |

说明：“测试调用智能体”由前端直接请求 **网关暴露的 URL**（见下），请求头带 `X-API-Key`，不经过 Admin Backend 的业务接口；Admin Backend 仅提供“我的 Key 列表”以便用户复制 Key 去测试。

### 5.2 Agent Service（智能体服务）

仅被 APISIX 转发调用，不对外直接暴露。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /chat | 请求体：{ "session_id": "?", "message": "?" }；响应：{ "reply": "?", "session_id": "?" }；内部写 conversation/message |
| GET | /health | 健康检查 |

可选：GET /chat/sessions/:session_id/messages 用于拉历史（演示可先不做）。

### 5.3 经网关暴露给用户的智能体 API（由 APISIX 配置）

| 方法 | 网关路径 | 后端实际路径 | 说明 |
|------|----------|--------------|------|
| POST | /v1/chat | 转发到 Agent Service 的 /chat | 用户请求需带 X-API-Key |

---

## 6. APISIX 在本项目中的职责与配置思路

### 6.1 职责

- **路由**：将 `/v1/chat` 等请求转发到 Agent Service。
- **鉴权**：使用 **key-auth** 插件，从 Header `X-API-Key`（或 `apikey`）取 Key，校验是否匹配某 Consumer；未匹配则 401。
- **限流**：使用 **limit-count** 插件，按 Consumer 维度、固定时间窗口（如 1 分钟）限制请求次数；超出返回 429。
- **配置存储**：routes、consumers、plugins 存于 **etcd**；APISIX 从 etcd 读取，无需手改本地文件即可生效。

### 6.2 配置思路

- **全局/默认**：可在 config.yaml 中配置 etcd 地址、日志等。
- **Route**：  
  - 例如 `uri = /v1/chat`，`methods = POST`，`upstream` 指向 Agent Service（如 `http://agent-service:8000`）。  
  - 在该 Route 上绑定 **key-auth** 与 **limit-count**（或将 limit-count 绑定到 Consumer，见下）。
- **Consumer**：  
  - 每个发放的 API Key 对应一个 Consumer，`username` 可为 `consumer_{api_key_id}` 或唯一业务 ID。  
  - 在 Consumer 上配置 **key-auth** 的 key 值（即发放给用户的 API Key 明文，或 APISIX 支持的多 Key）。  
  - 在 Consumer 上配置 **limit-count**：`count = 配额值`，`time_window = 60`，`rejected_code = 429`。  
  - 这样“管理员修改配额”即：Admin Backend 调用 APISIX Admin API 更新该 Consumer 的 limit-count 配置。
- **同步时机**：  
  - **发放 Key**：Admin Backend 在审批通过后调用 APISIX Admin API 创建 Consumer（含 key-auth + limit-count）。  
  - **改配额**：Admin Backend 调用 APISIX Admin API 更新该 Consumer 的 limit-count 的 `count`。  
  - **撤销 Key**：可删除 Consumer 或禁用该 Route 对该 Consumer 的放行（演示简化可直接删除 Consumer）。

### 6.3 Admin API 使用要点

- APISIX Admin API 默认端口 9180，需在 Docker 内网可访问（Admin Backend 调用）。  
- 创建 Consumer：`PUT /apisix/admin/consumers/{id}`，body 含 `plugins.key-auth`、`plugins.limit-count`。  
- 更新 Consumer：同 PUT，覆盖对应插件配置。  
- 删除 Consumer：`DELETE /apisix/admin/consumers/{id}`。  
- Route 的 `plugins` 中启用 `key-auth` 即可，具体 key 在 Consumer 上。

---

## 7. 推荐的开发顺序

1. **基础设施**  
   - 编写 `docker-compose.yml`：etcd、APISIX、Admin Backend、Agent Service、Frontend（可选先本地 dev）。  
   - 确认 APISIX 能连 etcd、能通过 Admin API 创建 Route/Consumer。

2. **Agent Service**  
   - 建表（conversation、message）、实现 `POST /chat` 与对话落库、简单模拟回复。  
   - 实现 `GET /health`。  
   - 在 Compose 中验证单独访问 Agent Service 正常。

3. **APISIX 基础路由与鉴权**  
   - 配置一条到 Agent Service 的 Route（如 `/v1/chat`）。  
   - 为该 Route 启用 key-auth；在 etcd/Admin API 中手写一个测试 Consumer 与 key，用 curl 带 `X-API-Key` 验证 200/401。

4. **Admin Backend — 数据与申请流**  
   - 建库建表（user、api_key_application、api_key、quota）。  
   - 实现申请 CRUD、我的申请列表（用户侧）。  
   - 实现管理员审批列表、审批通过/拒绝（状态更新）；审批通过时仅写 DB，暂不发放真实 Key 或同步 APISIX 也可。

5. **Admin Backend — Key 发放与 APISIX 同步**  
   - 审批通过时生成 API Key（随机）、写入 api_key、创建/更新 quota 默认值。  
   - 调用 APISIX Admin API 创建 Consumer（key-auth + limit-count），与 api_key 记录对应。  
   - 实现“管理员修改配额”：更新 DB + 调用 APISIX 更新该 Consumer 的 limit-count。

6. **Admin Backend — 用户 Key 与撤销**  
   - 用户侧：我的 Key 列表、撤销自己的 Key（DB + 删除/禁用 APISIX Consumer）。  
   - 管理员侧：Key 列表、管理员撤销。

7. **Frontend**  
   - 用户：申请页、我的申请、我的 Key、测试调用（输入 Key，请求网关 `POST /v1/chat`）。  
   - 管理员：审批页、Key 管理页、配额修改页。  
   - 环境变量区分 Admin Backend 与 Gateway 的 base URL。

8. **联调与演示**  
   - 端到端：申请 → 审批 → 用 Key 调网关 → 改配额 → 再调网关验证限流。  
   - 文档：README 中说明启动顺序、默认端口、示例 API Key（若存在）及注意事项。

---

以上设计满足“演示清晰、结构规范、便于扩展”，且各模块职责与数据流明确；实现时可按上述开发顺序迭代，先打通主流程再完善错误处理与前端体验。
