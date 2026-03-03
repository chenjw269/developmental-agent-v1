#!/bin/sh
# 手动初始化 APISIX 默认路由（当 apisix-init 服务未执行或需重建时）
# 用法: APISIX_ADMIN_URL=http://localhost:9180 APISIX_ADMIN_KEY=xxx ./scripts/apisix-init-route.sh

set -e
url="${APISIX_ADMIN_URL:-http://localhost:9180}"
key="${APISIX_ADMIN_KEY:?set APISIX_ADMIN_KEY}"

echo "Creating upstream (mock-agent-service)..."
curl -s -X PUT "${url}/apisix/admin/upstreams/1" \
  -H "X-API-KEY: ${key}" \
  -H "Content-Type: application/json" \
  -d '{"type":"roundrobin","nodes":[{"host":"mock-agent-service","port":8000,"weight":1}]}'
echo ""

echo "Creating route /agent/chat..."
curl -s -X PUT "${url}/apisix/admin/routes/1" \
  -H "X-API-KEY: ${key}" \
  -H "Content-Type: application/json" \
  -d '{"uri":"/agent/chat","name":"agent-chat","methods":["POST","GET"],"upstream_id":"1","plugins":{"key-auth":{}}}'
echo ""

echo "Done. Test: curl -X POST http://localhost:9080/agent/chat -H 'X-API-KEY: <your-key>' -H 'Content-Type: application/json' -d '{}'"
