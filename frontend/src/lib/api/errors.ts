export type FieldError = { loc: string[]; msg: string; type: string }

/** An error response from the API (RFC 9457 problem+json) or a network failure (status 0). */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string
  readonly requestId: string | null
  readonly fieldErrors: FieldError[]
  readonly retryAfterSeconds: number | null

  constructor(init: {
    status: number
    detail?: string
    requestId?: string | null
    fieldErrors?: FieldError[]
    retryAfterSeconds?: number | null
  }) {
    super(init.detail ?? `Request failed (${init.status})`)
    this.name = 'ApiError'
    this.status = init.status
    this.detail = init.detail ?? ''
    this.requestId = init.requestId ?? null
    this.fieldErrors = init.fieldErrors ?? []
    this.retryAfterSeconds = init.retryAfterSeconds ?? null
  }
}

export function networkError(): ApiError {
  return new ApiError({ status: 0, detail: 'Network error' })
}

type Problem = {
  detail?: unknown
  request_id?: unknown
  errors?: unknown
}

export function toApiError(body: unknown, response: Response): ApiError {
  const problem: Problem = typeof body === 'object' && body !== null ? (body as Problem) : {}
  const retry = Number(response.headers.get('Retry-After'))
  return new ApiError({
    status: response.status,
    detail: typeof problem.detail === 'string' ? problem.detail : undefined,
    requestId: typeof problem.request_id === 'string' ? problem.request_id : null,
    fieldErrors: Array.isArray(problem.errors) ? (problem.errors as FieldError[]) : [],
    retryAfterSeconds: Number.isFinite(retry) && retry > 0 ? retry : null,
  })
}

type Result<T> = { data?: T; error?: unknown; response: Response }

/** Await an openapi-fetch call; return its data or throw an ApiError. */
export async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  let result: Result<T>
  try {
    result = await call
  } catch {
    throw networkError()
  }
  if (result.error !== undefined || !result.response.ok) {
    throw toApiError(result.error, result.response)
  }
  return result.data as T
}

/** User-facing text. Never shows raw server details, which can be technical. */
export function friendlyMessage(err: unknown, fallbackFor401?: string): string {
  if (!(err instanceof ApiError)) return 'Something went wrong. Please try again.'
  if (err.status === 0) return "Can't reach the server. Check your connection and try again."
  if (err.status === 429) {
    const minutes = err.retryAfterSeconds
      ? Math.max(1, Math.ceil(err.retryAfterSeconds / 60))
      : null
    return minutes
      ? `Too many attempts. Try again in ${minutes} minute${minutes === 1 ? '' : 's'}.`
      : 'Too many attempts. Please try again later.'
  }
  if (err.status === 401 && fallbackFor401) return fallbackFor401
  if (err.status === 403 && /not verified/i.test(err.detail)) {
    return 'Please verify your email first. Check your inbox for the link.'
  }
  if (err.status === 400 && /invalid or has expired|invalid or expired/i.test(err.detail)) {
    return 'This link is invalid or has expired.'
  }
  return 'Something went wrong. Please try again.'
}
