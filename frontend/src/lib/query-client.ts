import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api/errors'

/** Retrying cannot fix a client error (not found, forbidden, rate limited), so do not. */
const NO_RETRY_STATUS = new Set([400, 401, 403, 404, 409, 422, 429])

export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && NO_RETRY_STATUS.has(error.status)) return false
  return failureCount < 1
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: shouldRetry, refetchOnWindowFocus: false },
    },
  })
}
