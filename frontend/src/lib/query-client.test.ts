import { ApiError } from '@/lib/api/errors'
import { shouldRetry } from './query-client'

describe('shouldRetry', () => {
  it.each([400, 401, 403, 404, 409, 422, 429])('never retries HTTP %s', (status) => {
    expect(shouldRetry(0, new ApiError({ status }))).toBe(false)
  })

  it.each([0, 500, 502, 503])('retries HTTP %s once', (status) => {
    expect(shouldRetry(0, new ApiError({ status }))).toBe(true)
    expect(shouldRetry(1, new ApiError({ status }))).toBe(false)
  })

  it('retries unknown errors once', () => {
    expect(shouldRetry(0, new Error('boom'))).toBe(true)
    expect(shouldRetry(1, new Error('boom'))).toBe(false)
  })
})
