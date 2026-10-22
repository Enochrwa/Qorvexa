import { http, HttpResponse } from 'msw'
import { API, server } from '@/test/server'
import { api } from './client'
import { ApiError, friendlyMessage, unwrap } from './errors'
import { useSession } from './session'

const ME = { id: 'u1', email: 'a@example.com', role: 'viewer', email_verified: true }

function signedIn(token = 'old-token') {
  useSession.setState({ status: 'authenticated', accessToken: token, user: null })
}

describe('api client', () => {
  it('sends the in-memory access token as a bearer header', async () => {
    signedIn('abc')
    let seen: string | null = null
    server.use(
      http.get(`${API}/auth/me`, ({ request }) => {
        seen = request.headers.get('Authorization')
        return HttpResponse.json(ME)
      }),
    )
    await unwrap(api.GET('/api/v1/auth/me'))
    expect(seen).toBe('Bearer abc')
  })

  it('refreshes once on 401 and retries the original request with the new token', async () => {
    signedIn('old-token')
    const calls: string[] = []
    server.use(
      http.get(`${API}/auth/me`, ({ request }) => {
        const auth = request.headers.get('Authorization')
        calls.push(`me:${auth}`)
        return auth === 'Bearer new-token'
          ? HttpResponse.json(ME)
          : HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
      }),
      http.post(`${API}/auth/refresh`, ({ request }) => {
        calls.push(`refresh:${request.headers.get('X-Qorvexa-Client')}`)
        return HttpResponse.json({
          access_token: 'new-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }),
    )
    const me = await unwrap(api.GET('/api/v1/auth/me'))
    expect(me.email).toBe('a@example.com')
    expect(calls).toEqual(['me:Bearer old-token', 'refresh:web', 'me:Bearer new-token'])
    expect(useSession.getState().accessToken).toBe('new-token')
  })

  it('shares ONE refresh request between concurrent 401s', async () => {
    signedIn('old-token')
    let refreshes = 0
    server.use(
      http.get(`${API}/auth/me`, ({ request }) =>
        request.headers.get('Authorization') === 'Bearer new-token'
          ? HttpResponse.json(ME)
          : HttpResponse.json({ detail: 'expired' }, { status: 401 }),
      ),
      http.post(`${API}/auth/refresh`, async () => {
        refreshes += 1
        await new Promise((r) => setTimeout(r, 30)) // keep it in flight while the others fail
        return HttpResponse.json({
          access_token: 'new-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }),
    )
    const results = await Promise.all(
      Array.from({ length: 6 }, () => unwrap(api.GET('/api/v1/auth/me'))),
    )
    expect(results).toHaveLength(6)
    expect(refreshes).toBe(1)
  })

  it('clears the session and gives up (no loop) when the refresh is rejected', async () => {
    signedIn('old-token')
    let refreshes = 0
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ detail: 'expired' }, { status: 401 })),
      http.post(`${API}/auth/refresh`, () => {
        refreshes += 1
        return HttpResponse.json({ detail: 'Invalid session' }, { status: 401 })
      }),
    )
    await expect(unwrap(api.GET('/api/v1/auth/me'))).rejects.toMatchObject({ status: 401 })
    expect(refreshes).toBe(1)
    expect(useSession.getState()).toMatchObject({ status: 'anonymous', accessToken: null })
  })

  it('does not refresh when login itself returns 401', async () => {
    let refreshes = 0
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 }),
      ),
      http.post(`${API}/auth/refresh`, () => {
        refreshes += 1
        return HttpResponse.json({}, { status: 401 })
      }),
    )
    await expect(
      unwrap(api.POST('/api/v1/auth/login', { body: { email: 'a@example.com', password: 'x' } })),
    ).rejects.toMatchObject({ status: 401 })
    expect(refreshes).toBe(0)
  })

  it('keeps the session when the refresh fails because the network is down', async () => {
    signedIn('old-token')
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ detail: 'expired' }, { status: 401 })),
      http.post(`${API}/auth/refresh`, () => HttpResponse.error()),
    )
    await expect(unwrap(api.GET('/api/v1/auth/me'))).rejects.toMatchObject({ status: 401 })
    expect(useSession.getState().status).toBe('authenticated') // not logged out by an outage
  })

  it('turns network failures into an ApiError with status 0', async () => {
    server.use(http.get(`${API}/genres`, () => HttpResponse.error()))
    const err = await unwrap(api.GET('/api/v1/genres')).catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(0)
  })

  it('never writes the access token to browser storage or cookies', async () => {
    server.use(
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({
          access_token: 'secret-token-value',
          token_type: 'bearer',
          expires_in: 900,
        }),
      ),
      http.get(`${API}/auth/me`, () => HttpResponse.json(ME)),
    )
    const { login } = await import('@/features/auth/api')
    await login('a@example.com', 'a-long-enough-pass')
    expect(useSession.getState().accessToken).toBe('secret-token-value')
    const dump =
      JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }) + document.cookie
    expect(dump).not.toContain('secret-token-value')
    expect(localStorage.length + sessionStorage.length).toBe(0)
  })
})

describe('error handling', () => {
  it('parses problem+json including field errors and Retry-After', async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          {
            detail: 'Invalid request',
            request_id: 'req-1',
            errors: [
              { loc: ['body', 'password'], msg: 'Password is too common', type: 'value_error' },
            ],
          },
          {
            status: 422,
            headers: { 'Content-Type': 'application/problem+json', 'Retry-After': '120' },
          },
        ),
      ),
    )
    const err = (await unwrap(
      api.POST('/api/v1/auth/register', {
        body: { email: 'a@example.com', password: 'password123' },
      }),
    ).catch((e: unknown) => e)) as ApiError
    expect(err.status).toBe(422)
    expect(err.requestId).toBe('req-1')
    expect(err.fieldErrors[0]).toMatchObject({ msg: 'Password is too common' })
    expect(err.retryAfterSeconds).toBe(120)
  })

  it('writes friendly messages and never leaks server detail', () => {
    const mk = (status: number, detail = '', retryAfterSeconds: number | null = null) =>
      new ApiError({ status, detail, retryAfterSeconds })
    expect(friendlyMessage(mk(0))).toMatch(/can't reach the server/i)
    expect(friendlyMessage(mk(429, '', 600))).toBe('Too many attempts. Try again in 10 minutes.')
    expect(friendlyMessage(mk(429, '', 30))).toBe('Too many attempts. Try again in 1 minute.')
    expect(friendlyMessage(mk(429))).toMatch(/try again later/i)
    expect(friendlyMessage(mk(401), 'Incorrect email or password.')).toBe(
      'Incorrect email or password.',
    )
    expect(friendlyMessage(mk(403, 'Email not verified'))).toMatch(/verify your email/i)
    expect(friendlyMessage(mk(400, 'Invalid or expired token'))).toMatch(/invalid or has expired/i)
    expect(friendlyMessage(mk(500, 'Traceback: secret internals'))).toBe(
      'Something went wrong. Please try again.',
    )
    expect(friendlyMessage(new Error('boom'))).toBe('Something went wrong. Please try again.')
  })
})
