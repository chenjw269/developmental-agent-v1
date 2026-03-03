import type {
  ApplicationCreate,
  Application,
  ApplicationListResponse,
  ApproveResponse,
} from '../types'
import { adminGet, adminPost, adminDelete, ApiError } from './client'

const BASE = '/api/v1/applications'

/** 用户：提交申请 */
export async function createApplication(
  data: ApplicationCreate,
  adminKey?: string | null
): Promise<Application> {
  try {
    return await adminPost<Application, ApplicationCreate>(BASE, data, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：获取申请列表 */
export async function listApplications(
  params: { status?: string; skip?: number; limit?: number } = {},
  adminKey?: string | null
): Promise<ApplicationListResponse> {
  const sp = new URLSearchParams()
  if (params.status) sp.set('status', params.status)
  if (params.skip != null) sp.set('skip', String(params.skip))
  if (params.limit != null) sp.set('limit', String(params.limit))
  const q = sp.toString()
  const path = q ? `${BASE}?${q}` : BASE
  try {
    return await adminGet<ApplicationListResponse>(path, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：审批通过 */
export async function approveApplication(
  applicationId: number,
  adminKey?: string | null
): Promise<ApproveResponse> {
  try {
    return await adminPost<ApproveResponse>(
      `${BASE}/${applicationId}/approve`,
      undefined,
      adminKey
    )
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：拒绝 */
export async function rejectApplication(
  applicationId: number,
  adminKey?: string | null
): Promise<{ message: string; application_id: number }> {
  try {
    return await adminPost<{ message: string; application_id: number }>(
      `${BASE}/${applicationId}/reject`,
      undefined,
      adminKey
    )
  } catch (e) {
    throw e as ApiError
  }
}

/** 管理员：永久删除申请（已通过的会同时删除 API Key 与 APISIX Consumer） */
export async function deleteApplication(
  applicationId: number,
  adminKey?: string | null
): Promise<{ message: string; application_id: number }> {
  try {
    return await adminDelete(`${BASE}/${applicationId}`, adminKey)
  } catch (e) {
    throw e as ApiError
  }
}
