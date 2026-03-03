import type { CredentialListResponse } from '../types'
import { adminGet, adminPost, adminPatch, adminDelete, ApiError } from './client'

const BASE = '/api/v1/credentials'

/** 管理员：获取凭证列表 */
export async function listCredentials(
  params: { skip?: number; limit?: number; active_only?: boolean } = {},
  adminKey?: string | null
): Promise<CredentialListResponse> {
  const sp = new URLSearchParams()
  if (params.skip != null) sp.set('skip', String(params.skip))
  if (params.limit != null) sp.set('limit', String(params.limit))
  if (params.active_only != null) sp.set('active_only', String(params.active_only))
  const q = sp.toString()
  const path = q ? `${BASE}?${q}` : BASE
  try {
    return await adminGet<CredentialListResponse>(path, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：修改配额 */
export async function updateQuota(
  credentialId: number,
  quotaPerMinute: number,
  adminKey?: string | null
): Promise<unknown> {
  try {
    return await adminPatch(
      `${BASE}/${credentialId}/quota`,
      { quota_per_minute: quotaPerMinute },
      adminKey
    )
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：修改 token 余额（按 credential id） */
export async function updateBalance(
  credentialId: number,
  tokenBalance: number,
  adminKey?: string | null
): Promise<unknown> {
  try {
    return await adminPatch(
      `${BASE}/${credentialId}/balance`,
      { token_balance: tokenBalance },
      adminKey
    )
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：按 API Key(consumer_name) 或用户名设置 token 数量 */
export async function setBalanceByTarget(
  params: { consumer_name?: string; username?: string; token_balance: number },
  adminKey?: string | null
): Promise<{ message: string; target: string; value: string; token_balance: number; updated: unknown[] }> {
  const body: { consumer_name?: string; username?: string; token_balance: number } = {
    token_balance: params.token_balance,
  }
  if (params.consumer_name != null && params.consumer_name.trim() !== '') {
    body.consumer_name = params.consumer_name.trim()
  } else if (params.username != null && params.username.trim() !== '') {
    body.username = params.username.trim()
  }
  try {
    return await adminPost(
      `${BASE}/set-balance`,
      body,
      adminKey
    ) as { message: string; target: string; value: string; token_balance: number; updated: unknown[] }
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：禁用 */
export async function disableCredential(
  credentialId: number,
  adminKey?: string | null
): Promise<unknown> {
  try {
    return await adminPatch(`${BASE}/${credentialId}/disable`, undefined, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：启用 */
export async function enableCredential(
  credentialId: number,
  adminKey?: string | null
): Promise<unknown> {
  try {
    return await adminPatch(`${BASE}/${credentialId}/enable`, undefined, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：永久删除 API Key（从 APISIX 与数据库移除） */
export async function deleteCredential(
  credentialId: number,
  adminKey?: string | null
): Promise<unknown> {
  try {
    return await adminDelete(`${BASE}/${credentialId}`, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}
