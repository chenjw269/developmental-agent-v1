# 多阶段：先构建 React 应用，再由 nginx  serving
# 使用 AWS ECR 公共镜像，避免 Docker Hub 连接超时

# 阶段 1：构建
FROM public.ecr.aws/docker/library/node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
# 构建时注入的 URL（可选，默认已在 config.ts 写 localhost）
ARG VITE_ADMIN_API_BASE=
ARG VITE_GATEWAY_BASE=
ENV VITE_ADMIN_API_BASE=$VITE_ADMIN_API_BASE
ENV VITE_GATEWAY_BASE=$VITE_GATEWAY_BASE
RUN npm run build

# 阶段 2：运行
FROM public.ecr.aws/docker/library/nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
