import { GATEWAY_BASE, AGENT_CHAT_PATH, API_KEY_HEADER } from '../config'
import type { AgentChatRequest, AgentChatResponse } from '../types'

const url = `${GATEWAY_BASE}${AGENT_CHAT_PATH}`

/**
 * 通过 APISIX 网关调用智能体聊天（需 API Key）
 * 超限时网关返回 429，此处抛出包含 status 和 message 的错误
 */
export async function postAgentChat(
  apiKey: string,
  body: AgentChatRequest
): Promise<AgentChatResponse> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      [API_KEY_HEADER]: apiKey,
    },
    body: JSON.stringify(body),
  })
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = {}
  }
  if (!res.ok) {
    const message =
      res.status === 429
        ? '请求过于频繁，已超过每分钟配额限制，请稍后再试。'
        : res.status === 402
          ? (data as { detail?: string }).detail ?? 'Token 余额已耗尽，请联系管理员充值。'
          : (data as { message?: string }).message ?? (text || res.statusText)
    throw { message, status: res.status, detail: text }
  }
  return data as AgentChatResponse
}
