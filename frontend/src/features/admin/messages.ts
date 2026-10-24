import { ApiError, friendlyMessage } from '@/lib/api/errors'

/**
 * Admin screens are for trusted staff, and the API's 409/422 messages are our own plain
 * sentences ("Title is not ready to publish: missing synopsis"), so show them. Everything
 * else keeps the safe generic text.
 */
export function adminMessage(err: unknown): string {
  if (err instanceof ApiError && (err.status === 409 || err.status === 422) && err.detail) {
    return err.detail
  }
  if (err instanceof ApiError && err.status === 403) return 'You do not have permission to do that.'
  return friendlyMessage(err)
}
