import { ADMIN_API_BASE, ADMIN_HEADER_KEY } from '../config'

export type ApiError = { message: string; status?: number; detail?: string }

async function handleResponse<T>(res: Response): Promise<T> {
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { detail: text || res.statusText }
  }
  if (!res.ok) {
    const detail = typeof (data as { detail?: string }).detail === 'string'
      ? (data as { detail: string }).detail
      : JSON.stringify((data as { detail?: unknown }).detail ?? data)
    throw { message: detail || res.statusText, status: res.status, detail } as ApiError
  }
  return data as T
}

/** 带可选 Admin Key 的 GET */
export async function adminGet<T>(
  path: string,
  adminKey?: string | null
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (adminKey) headers[ADMIN_HEADER_KEY] = adminKey
  const res = await fetch(`${ADMIN_API_BASE}${path}`, { method: 'GET', headers })
  return handleResponse<T>(res)
}

/** 带可选 Admin Key 的 POST */
export async function adminPost<T, B = unknown>(
  path: string,
  body?: B,
  adminKey?: string | null
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (adminKey) headers[ADMIN_HEADER_KEY] = adminKey
  const res = await fetch(`${ADMIN_API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

/** 带可选 Admin Key 的 PATCH */
export async function adminPatch<T, B = unknown>(
  path: string,
  body?: B,
  adminKey?: string | null
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (adminKey) headers[ADMIN_HEADER_KEY] = adminKey
  const res = await fetch(`${ADMIN_API_BASE}${path}`, {
    method: 'PATCH',
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  return handleResponse<T>(res)
}

/** 带可选 Admin Key 的 DELETE */
export async function adminDelete<T = unknown>(
  path: string,
  adminKey?: string | null
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (adminKey) headers[ADMIN_HEADER_KEY] = adminKey
  const res = await fetch(`${ADMIN_API_BASE}${path}`, { method: 'DELETE', headers })
  return handleResponse<T>(res)
}
