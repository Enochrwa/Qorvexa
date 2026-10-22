import createClient from 'openapi-fetch'
import type { paths } from '@/types/api'
import { useSession } from './session'

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
export const CSRF_HEADER = { 'X-Qorvexa-Client': 'web' } as const

/** Auth endpoints that must never trigger a refresh-and-retry on 401. */
const NO_RETRY = [
  '/api/v1/auth/login',
  '/api/v1/auth/register',
  '/api/v1/auth/refresh',
  '/api/v1/auth/verify-email',
  '/api/v1/auth/password/',
]

let inflight: Promise<boolean> | null = null

/**
 * Get a new access token using the httpOnly refresh cookie.
 * Concurrent callers share ONE request: refresh tokens rotate, so a second parallel
 * request would replay a used token and sign the user out.
 */
export function refreshSession(): Promise<boolean> {
  inflight ??= doRefresh().finally(() => {
    inflight = null
  })
  return inflight
}

async function doRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: CSRF_HEADER,
    })
    if (!res.ok) {
      useSession.getState().clear()
      return false
    }
    const body = (await res.json()) as { access_token: string }
    useSession.getState().setToken(body.access_token)
    return true
  } catch {
    return false // offline: keep the session, the caller sees the original error
  }
}

const authFetch = async (request: Request): Promise<Response> => {
  const retry = request.clone()
  const token = useSession.getState().accessToken
  if (token) request.headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(request)
  const path = new URL(request.url).pathname
  if (response.status !== 401 || NO_RETRY.some((p) => path.startsWith(p))) return response
  if (!(await refreshSession())) return response
  const fresh = useSession.getState().accessToken
  if (fresh) retry.headers.set('Authorization', `Bearer ${fresh}`)
  return fetch(retry)
}

export const api = createClient<paths>({
  baseUrl: API_URL,
  credentials: 'include',
  fetch: authFetch,
})
