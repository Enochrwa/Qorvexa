import { api, CSRF_HEADER, refreshSession } from '@/lib/api/client'
import { unwrap } from '@/lib/api/errors'
import { useProfile } from '@/features/profiles/store'
import { useSession } from '@/lib/api/session'

export async function loadMe() {
  const me = await unwrap(api.GET('/api/v1/auth/me'))
  useSession.getState().setUser(me)
  useProfile.getState().hydrate(me.id)
  return me
}

export async function login(email: string, password: string) {
  const token = await unwrap(api.POST('/api/v1/auth/login', { body: { email, password } }))
  useSession.getState().setToken(token.access_token)
  return loadMe()
}

export async function register(email: string, password: string) {
  await unwrap(api.POST('/api/v1/auth/register', { body: { email, password } }))
}

export async function verifyEmail(token: string) {
  await unwrap(api.POST('/api/v1/auth/verify-email', { body: { token } }))
}

export async function forgotPassword(email: string) {
  await unwrap(api.POST('/api/v1/auth/password/forgot', { body: { email } }))
}

export async function resetPassword(token: string, password: string) {
  await unwrap(api.POST('/api/v1/auth/password/reset', { body: { token, password } }))
}

export async function logout() {
  try {
    await unwrap(api.POST('/api/v1/auth/logout', { headers: CSRF_HEADER }))
  } finally {
    useSession.getState().clear() // always sign out locally, even if the request failed
    useProfile.getState().reset()
  }
}

let restoring: Promise<void> | null = null

/** Restore a session on page load from the refresh cookie. Runs once, even under StrictMode. */
export function restoreSession(): Promise<void> {
  restoring ??= (async () => {
    if (await refreshSession()) {
      try {
        await loadMe()
        return
      } catch {
        /* fall through */
      }
    }
    useSession.getState().clear()
  })()
  return restoring
}

/** Test helper: forget the cached restore so each test starts clean. */
export function resetRestoreForTests() {
  restoring = null
}
