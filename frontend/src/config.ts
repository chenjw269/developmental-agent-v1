/**
 * 前端配置：API 与网关地址，便于本地 / Docker 环境切换
 */
const getBaseUrl = (key: string, fallback: string): string => {
  if (typeof import.meta.env !== 'undefined' && (import.meta.env as Record<string, string>)[key]) {
    return (import.meta.env as Record<string, string>)[key].replace(/\/$/, '')
  }
  return fallback.replace(/\/$/, '')
}

/** 管理后端 API 根地址（申请、审批、配额等） */
export const ADMIN_API_BASE = getBaseUrl('VITE_ADMIN_API_BASE', 'http://localhost:8000')

/** APISIX 网关地址（用户带 API Key 访问智能体） */
export const GATEWAY_BASE = getBaseUrl('VITE_GATEWAY_BASE', 'http://localhost:9080')

/** 智能体聊天接口路径（相对 GATEWAY_BASE） */
export const AGENT_CHAT_PATH = '/agent/chat'

/** 管理端请求头：X-Admin-Key（可选，与后端 ADMIN_API_KEY 一致） */
export const ADMIN_HEADER_KEY = 'X-Admin-Key'

/** 调用智能体时使用的 API Key 请求头 */
export const API_KEY_HEADER = 'X-API-KEY'
