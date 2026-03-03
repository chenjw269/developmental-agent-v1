# 基础设施：Docker Compose 运行方案

## 1. 各服务作用说明

| 服务 | 作用 |
|------|------|
| **etcd** | APISIX 的配置存储。路由、上游、Consumer、插件等均存于 etcd，APISIX 从 etcd 读取并热更新。 |
| **apisix** | API 网关。9080 对外代理流量（如 `/agent/chat`），9180 提供 Admin API 供 admin-backend 管理 Consumer/密钥/限额。 |
| **apisix-init** | 一次性任务：在 APISIX 就绪后创建 **Upstream(id=1)** 和 **Route(id=1, /agent/chat)**，并启用 key-auth。限流由各 Consumer 的 limit-count 控制。 |
| **mock-agent-service** | 模拟智能体后端。提供 `POST /agent/chat`，作为 APISIX 的 upstream 目标，用户不直连。 |
| **admin-backend** | 管理后端。处理申请、审批、发放 API Key、改配额、禁用/启用；通过 APISIX Admin API 同步 Consumer 与 limit-count。 |
| **frontend** | React 演示前端。构建后由 nginx 托管，提供申请、管理、测试调用等页面；访问端口 3000。 |

## 2. 网络关系

- 所有服务在同一网络 `app-net`。
- **用户/前端** → 访问 `apisix:9080`（对外暴露 9080）、`admin-backend:8000`（对外 8000）、`frontend:80`（对外 3000）。
- **admin-backend** → 访问 `apisix:9180`（Admin API）。
- **apisix** → 访问 `etcd:2379`（配置）、`mock-agent-service:8000`（上游）。
- **apisix-init** → 访问 `apisix:9180`（创建路由/上游）。

## 3. 端口区分

| 端口（宿主机） | 服务 | 说明 |
|----------------|------|------|
| 2379 | etcd | etcd 客户端 |
| 9080 | apisix | **代理流量**，请求带 X-API-KEY 访问 /agent/chat |
| 9180 | apisix | **Admin API**，仅 admin-backend 和 init 调用 |
| 8000 | admin-backend | 管理 API（申请、审批、配额等） |
| 8001 | mock-agent-service | 仅演示/调试直连，生产不暴露 |
| 3000 | frontend | 前端页 |

## 4. 环境变量与文件

- 项目根目录 **`.env`**：由 `docker-compose` 自动读取。请复制 `.env.example` 为 `.env`。
- **APISIX_ADMIN_KEY**：必须与 `infra/apisix/config.yaml` 中 `deployment.admin.admin_key[0].key` 一致，否则 Admin API 和 init 会鉴权失败。
- **ADMIN_API_KEY**（可选）：若设置，管理端接口需在请求头带 `X-Admin-Key: <ADMIN_API_KEY>`。

## 5. 启动步骤

```bash
# 在项目根目录
cp .env.example .env
# 如需修改 APISIX 密钥，同时改 .env 与 infra/apisix/config.yaml 中的 key

docker compose up -d

# 等待 apisix 健康后，执行一次 init（若 apisix-init 未自动成功）
docker compose run --rm apisix-init
```

## 6. 验证步骤

1. **etcd**  
   `docker compose exec etcd etcdctl endpoint health`

2. **APISIX Admin API**  
   `curl -s http://localhost:9180/apisix/admin/routes -H "X-API-KEY: $APISIX_ADMIN_KEY"`  
   应返回 JSON（含 id 1 的路由）。

3. **管理后端**  
   - 打开 http://localhost:8000/docs  
   - 提交申请：`POST /api/v1/applications`，body 如 `{"username":"test","email":"test@example.com","reason":"demo"}`  
   - 管理员审批：`POST /api/v1/applications/1/approve`（需带 `X-Admin-Key` 若已设置），响应中会有 `api_key`

4. **经网关调用智能体**  
   `curl -X POST http://localhost:9080/agent/chat -H "X-API-KEY: <上一步返回的 api_key>" -H "Content-Type: application/json" -d "{\"message\":\"hello\"}"`  
   应返回 mock-agent 的 JSON 回复。

5. **无 Key 或错误 Key**  
   `curl -s -o /dev/null -w "%{http_code}" http://localhost:9080/agent/chat`  
   应为 401。

6. **前端**  
   打开 http://localhost:3000 应看到 React 演示平台：首页、申请 API Key、管理后台、测试调用。

## 7. 初始化基础 Route 的两种方式

- **方式一（推荐）**：依赖 `apisix-init` 服务。`docker compose up -d` 后等 apisix 健康，init 会自动执行；若失败可再跑一次：`docker compose run --rm apisix-init`。
- **方式二**：在宿主机执行 `scripts/apisix-init-route.sh`，需先设置 `APISIX_ADMIN_URL=http://localhost:9180` 和 `APISIX_ADMIN_KEY=<与 config 一致>`。

初始化内容：创建 Upstream(id=1) → mock-agent-service:8000；创建 Route(id=1) → uri=/agent/chat，upstream_id=1，plugins.key-auth。

---

## 8. 前端与 Docker 结合

**frontend** 使用多阶段构建：

1. **构建阶段**：Node 镜像执行 `npm install` 和 `npm run build`，生成 `dist/`。
2. **运行阶段**：nginx 镜像将 `dist/` 拷贝到 `/usr/share/nginx/html`，并用 `nginx.conf` 提供 SPA 路由回退（`try_files` 到 `index.html`）。

前端运行在**用户浏览器**中，请求直接发往宿主机端口：
- 管理 API → `http://localhost:8000`（默认）
- 网关 → `http://localhost:9080`（默认）

在本地 `docker compose` 场景下，宿主机端口与容器映射一致，因此上述默认即可。

若部署到**非本机**（如远程服务器、其他域名），需在构建时传入环境变量：

```bash
docker compose build --build-arg VITE_ADMIN_API_BASE=https://api.example.com --build-arg VITE_GATEWAY_BASE=https://gateway.example.com frontend
```
