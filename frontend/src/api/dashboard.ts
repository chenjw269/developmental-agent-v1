import type { ApiError } from './client'
import { adminGet } from './client'

const BASE = '/api/v1/dashboard'

export interface DashboardUser {
  id: number
  username: string
  email: string
}

export interface DashboardStats {
  total_tokens: number
  used_tokens: number
  remaining_tokens: number
  user_id?: number
}

export interface DashboardSummary {
  applications: { pending: number; approved: number; rejected: number; total: number }
  credentials: { active: number }
  tokens: { total: number; used: number; remaining: number }
}

export async function getDashboardUsers(adminKey?: string | null): Promise<{ items: DashboardUser[] }> {
  try {
    return await adminGet<{ items: DashboardUser[] }>(`${BASE}/users`, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

export async function getDashboardStats(
  adminKey?: string | null,
  userId?: number | null
): Promise<DashboardStats> {
  const q = userId != null ? `?user_id=${userId}` : ''
  try {
    return await adminGet<DashboardStats>(`${BASE}/stats${q}`, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

export async function getDashboardSummary(adminKey?: string | null): Promise<DashboardSummary> {
  try {
    return await adminGet<DashboardSummary>(`${BASE}/summary`, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}
