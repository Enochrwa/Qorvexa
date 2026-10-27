import createClient from 'openapi-fetch'
import type { paths } from '@/types/api'
import { useProfile } from '@/features/profiles/store'
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

/** Endpoints that do not take the selected profile. */
const NO_PROFILE = ['/api/v1/auth/', '/api/v1/profiles', '/api/v1/admin/']

/** Attach credentials and, for profile-aware endpoints, the selected profile. */
function decorate(request: Request): void {
  const token = useSession.getState().accessToken
  if (!token) return
  request.headers.set('Authorization', `Bearer ${token}`)
  const profileId = useProfile.getState().selectedId
  const path = new URL(request.url).pathname
  if (profileId && !NO_PROFILE.some((p) => path.startsWith(p))) {
    request.headers.set('X-Profile-Id', profileId)
  }
}

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

const RETRY_DELAY_MS = 400

async function doRefresh(): Promise<boolean> {
  // A network failure (connection dropped, request aborted) is retried once: the server may
  // already have rotated the token, and it accepts a quick retry with the old one. An HTTP
  // rejection is final and is never retried.
  for (let attempt = 0; attempt < 2; attempt++) {
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
      if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS))
    }
  }
  return false // offline: keep the session, the caller sees the original error
}

const authFetch = async (request: Request): Promise<Response> => {
  const retry = request.clone()
  decorate(request)
  const response = await fetch(request)
  const path = new URL(request.url).pathname
  if (response.status !== 401 || NO_RETRY.some((p) => path.startsWith(p))) return response
  if (!(await refreshSession())) return response
  decorate(retry)
  return fetch(retry)
}

export const api = createClient<paths>({
  baseUrl: API_URL,
  credentials: 'include',
  fetch: authFetch,
})
