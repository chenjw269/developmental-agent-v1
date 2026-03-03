# APISIX 配置说明

## 本项目中 APISIX 的职责

- **数据面（9080）**：对外提供 `/agent/chat`，对请求做 **key-auth** 鉴权后转发到 mock-agent-service。
- **控制面（9180）**：Admin API，供 admin-backend 动态创建/更新/删除 **Consumer**（API Key + limit-count 限额）。

## Route / Upstream 在本项目中的配置

### Upstream（上游）

- **ID**: `1`（由 `apisix-init` 或脚本创建）
- **类型**: roundrobin
- **节点**: `mock-agent-service:8000`（Docker 服务名）
- 含义：所有匹配到的请求都会被转发到 mock-agent-service 的 8000 端口。

### Route（路由）

- **ID**: `1`
- **uri**: `/agent/chat`
- **methods**: `POST`, `GET`
- **upstream_id**: `1`
- **plugins**: `key-auth`（必须带合法 API Key，否则 401）

限流 **limit-count** 不在 Route 上，而在每个 **Consumer** 上（admin-backend 审批通过时为每个用户创建 Consumer 并配置 limit-count）。

### 初始化方式

1. **推荐**：`docker-compose up` 时自动运行 `apisix-init` 服务，向 Admin API 提交 Upstream 与 Route。
2. **备选**：若未跑 init 或需重建，可执行：
   ```bash
   APISIX_ADMIN_URL=http://localhost:9180 APISIX_ADMIN_KEY=edd1c9f034335f136f87ad84b625c8f1 ./scripts/apisix-init-route.sh
   ```
   或在容器内用相同参数调用脚本。

## 配置文件

- `config.yaml`：挂载到 APISIX 容器 `/usr/local/apisix/conf/config.yaml`。
- 其中 `deployment.etcd.host` 指向 `http://etcd:2379`，与 docker-compose 中服务名一致。
- `deployment.admin.admin_key` 需与 `.env` 中 `APISIX_ADMIN_KEY` 一致，供 admin-backend 和 init 脚本使用。
