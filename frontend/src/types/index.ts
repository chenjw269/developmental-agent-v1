/** 申请单 */
export interface Application {
  id: number
  user_id: number
  reason: string | null
  status: string
  created_at: string
  reviewed_at: string | null
  user_username: string | null
  user_email: string | null
}

export interface ApplicationListResponse {
  items: Application[]
  total: number
}

/** 创建申请 */
export interface ApplicationCreate {
  username: string
  email: string
  reason?: string
}

/** 凭证（API Key） */
export interface Credential {
  id: number
  user_id: number
  application_id: number | null
  consumer_name: string
  api_key: string
  quota_per_minute: number
  token_balance: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CredentialListResponse {
  items: Credential[]
  total: number
}

/** 审批通过返回（含一次性 api_key） */
export interface ApproveResponse {
  message: string
  application_id: number
  credential_id: number
  api_key: string
  consumer_name: string
  quota_per_minute: number
  token_balance: number
}

/** 智能体聊天请求/响应 */
export interface AgentChatRequest {
  message: string
}

export interface AgentChatResponse {
  reply: string
  consumer: string
  stored: boolean
  remaining_tokens?: number
}
