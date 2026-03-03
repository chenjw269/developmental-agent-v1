# 智能体 API 网关演示 - 前端

React + Vite + TypeScript 演示界面，用于「申请 API Key → 管理员审批 → 带 Key 访问智能体 → 管理员调整配额」闭环。

## 目录结构

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── config.ts           # ADMIN_API_BASE, GATEWAY_BASE 等
│   ├── vite-env.d.ts
│   ├── types/
│   │   └── index.ts         # Application, Credential, AgentChat 等类型
│   ├── api/
│   │   ├── client.ts        # adminGet / adminPost / adminPatch
│   │   ├── applications.ts # 申请、审批、拒绝
│   │   ├── credentials.ts  # 凭证列表、配额、禁用/启用
│   │   └── agent.ts         # 经网关调用智能体聊天
│   ├── pages/
│   │   ├── Home.tsx         # 首页与三条入口
│   │   ├── Apply.tsx        # 用户申请 API Key
│   │   ├── Admin.tsx        # 管理后台（申请列表、凭证、配额、禁用/启用）
│   │   └── TestCall.tsx     # 测试调用智能体（含超限提示）
│   └── ...
├── public/                  # 静态资源（若保留）
└── Dockerfile               # 多阶段：build + nginx 或保留原静态
```

## 页面与路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Home | 系统介绍 + 申请 / 管理 / 测试 三个入口卡片 |
| `/apply` | Apply | 用户名、邮箱、申请原因，提交申请 |
| `/admin` | Admin | 管理员密钥、申请列表（通过/拒绝）、凭证列表（配额、禁用/启用） |
| `/test` | TestCall | 输入 API Key 与消息，经网关调用智能体，展示结果或 429/401 提示 |

## 配置

- **开发**：`vite.config.ts` 中已配置 proxy，`/api` → 8000，`/agent` → 9080；也可在 `src/config.ts` 中直接写后端/网关地址。
- **生产/ Docker**：通过环境变量注入：
  - `VITE_ADMIN_API_BASE`：管理后端根地址（如 `http://localhost:8000`）
  - `VITE_GATEWAY_BASE`：网关地址（如 `http://localhost:9080`）
  构建时生效，见 `src/config.ts`。

## 启动方式

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:3000 。

构建：

```bash
npm run build
```

产物在 `dist/`，可交由 nginx 或 Docker 镜像托管。
