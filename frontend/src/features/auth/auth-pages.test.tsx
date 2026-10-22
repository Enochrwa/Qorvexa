import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { useSession } from '@/lib/api/session'
import { API, server } from '@/test/server'
import { ME, renderApp } from '@/test/render'
import { restoreSession } from './api'
import { RequireAuth } from './guards'

const TOKEN = { access_token: 'tok-1', token_type: 'bearer', expires_in: 900 }
const PASSWORD = 'a-long-enough-pass'

async function fill(label: string, value: string) {
  await userEvent.type(screen.getByLabelText(label), value)
}

describe('login', () => {
  it('shows validation errors without calling the API', async () => {
    renderApp('/login')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Enter your email')).toBeInTheDocument()
    expect(screen.getByText('Enter your password')).toBeInTheDocument()
    await fill('Email', 'not-an-email')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Enter a valid email')).toBeInTheDocument()
  })

  it('signs in, loads the user and goes home', async () => {
    server.use(
      http.post(`${API}/auth/login`, async ({ request }) => {
        expect(await request.json()).toEqual({ email: 'viewer@example.com', password: PASSWORD })
        return HttpResponse.json(TOKEN)
      }),
      http.get(`${API}/auth/me`, () => HttpResponse.json(ME)),
    )
    const { router } = renderApp('/login')
    await fill('Email', 'viewer@example.com')
    await fill('Password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
    expect(useSession.getState().status).toBe('authenticated')
    expect(await screen.findByText('viewer@example.com')).toBeInTheDocument()
  })

  it('returns to the page the user came from, but never to another site', async () => {
    server.use(
      http.post(`${API}/auth/login`, () => HttpResponse.json(TOKEN)),
      http.get(`${API}/auth/me`, () => HttpResponse.json(ME)),
    )
    const good = renderApp('/login?next=%2Fprofiles')
    await fill('Email', 'viewer@example.com')
    await fill('Password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(good.router.state.location.pathname).toBe('/profiles'))
    good.unmount()
    useSession.setState({ status: 'anonymous', accessToken: null, user: null })

    const evil = renderApp('/login?next=https%3A%2F%2Fevil.example.com')
    await fill('Email', 'viewer@example.com')
    await fill('Password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(evil.router.state.location.pathname).toBe('/'))
  })

  it.each([
    [401, { detail: 'Invalid credentials' }, {}, 'Incorrect email or password.'],
    [403, { detail: 'Email not verified' }, {}, /verify your email first/i],
    [
      429,
      { detail: 'Too many requests' },
      { 'Retry-After': '900' },
      'Too many attempts. Try again in 15 minutes.',
    ],
    [
      500,
      { detail: 'Traceback (most recent call last)' },
      {},
      'Something went wrong. Please try again.',
    ],
  ])('shows a safe message for HTTP %s', async (status, body, headers, expected) => {
    server.use(http.post(`${API}/auth/login`, () => HttpResponse.json(body, { status, headers })))
    renderApp('/login')
    await fill('Email', 'viewer@example.com')
    await fill('Password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(expected)
    expect(alert).not.toHaveTextContent(/traceback|invalid credentials/i)
    expect(useSession.getState().accessToken).toBeNull()
  })

  it('redirects signed-in users away from the login page', async () => {
    useSession.setState({ status: 'authenticated', accessToken: 't', user: ME })
    const { router } = renderApp('/login')
    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  })

  it('uses the right autocomplete hints for password managers', () => {
    renderApp('/login')
    expect(screen.getByLabelText('Email')).toHaveAttribute('autocomplete', 'username')
    expect(screen.getByLabelText('Password')).toHaveAttribute('autocomplete', 'current-password')
  })
})

describe('register', () => {
  it('validates length and confirmation before calling the API', async () => {
    renderApp('/register')
    await fill('Email', 'new@example.com')
    await fill('Password', 'short')
    await fill('Confirm password', 'different')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Use at least 10 characters')).toBeInTheDocument()
  })

  it('flags a mismatched confirmation', async () => {
    renderApp('/register')
    await fill('Email', 'new@example.com')
    await fill('Password', PASSWORD)
    await fill('Confirm password', PASSWORD + 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument()
  })

  it('shows the same neutral confirmation whatever the server knows', async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json({ status: 'accepted' }, { status: 202 }),
      ),
    )
    renderApp('/register')
    await fill('Email', 'new@example.com')
    await fill('Password', PASSWORD)
    await fill('Confirm password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('status')).toHaveTextContent(
      /if new@example.com can be registered/i,
    )
  })

  it('shows a server-side password rule next to the field', async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          {
            detail: 'Invalid request',
            errors: [
              { loc: ['body', 'password'], msg: 'Password is too common', type: 'value_error' },
            ],
          },
          { status: 422 },
        ),
      ),
    )
    renderApp('/register')
    await fill('Email', 'new@example.com')
    await fill('Password', 'password123')
    await fill('Confirm password', 'password123')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByText('Password is too common')).toBeInTheDocument()
  })

  it('tells the user when registrations are rate limited', async () => {
    server.use(
      http.post(`${API}/auth/register`, () =>
        HttpResponse.json(
          { detail: 'Too many' },
          { status: 429, headers: { 'Retry-After': '3000' } },
        ),
      ),
    )
    renderApp('/register')
    await fill('Email', 'new@example.com')
    await fill('Password', PASSWORD)
    await fill('Confirm password', PASSWORD)
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Try again in 50 minutes')
  })
})

describe('verify email', () => {
  it('verifies once (even under StrictMode), strips the token from the URL and offers sign in', async () => {
    let calls = 0
    server.use(
      http.post(`${API}/auth/verify-email`, async ({ request }) => {
        calls += 1
        expect(await request.json()).toEqual({ token: 'verify-token-123' })
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { router } = renderApp('/verify-email?token=verify-token-123', { strict: true })
    expect(await screen.findByText(/your email is verified/i)).toBeInTheDocument()
    expect(calls).toBe(1)
    expect(router.state.location.search).toBe('')
    expect(screen.getByRole('link', { name: 'Go to sign in' })).toHaveAttribute('href', '/login')
  })

  it('explains an invalid or expired link', async () => {
    server.use(
      http.post(`${API}/auth/verify-email`, () =>
        HttpResponse.json({ detail: 'The link is invalid or has expired' }, { status: 400 }),
      ),
    )
    renderApp('/verify-email?token=expired-token-1')
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })

  it('fails immediately without a token and does not call the API', async () => {
    renderApp('/verify-email')
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })
})

describe('forgot and reset password', () => {
  it('forgot: always shows the neutral message', async () => {
    server.use(
      http.post(`${API}/auth/password/forgot`, () =>
        HttpResponse.json({ status: 'accepted' }, { status: 202 }),
      ),
    )
    renderApp('/forgot-password')
    await fill('Email', 'anyone@example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Send reset link' }))
    expect(await screen.findByRole('status')).toHaveTextContent(/if an account exists/i)
  })

  it('reset: changes the password and keeps the token out of the URL', async () => {
    server.use(
      http.post(`${API}/auth/password/reset`, async ({ request }) => {
        expect(await request.json()).toEqual({
          token: 'reset-token-123',
          password: 'another-long-password',
        })
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { router } = renderApp('/reset-password?token=reset-token-123')
    await waitFor(() => expect(router.state.location.search).toBe(''))
    await fill('New password', 'another-long-password')
    await fill('Confirm new password', 'another-long-password')
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByRole('status')).toHaveTextContent(/signed out everywhere/i)
  })

  it('reset: rejects a missing token and a bad link', async () => {
    renderApp('/reset-password')
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })

  it('reset: reports an expired link from the server', async () => {
    server.use(
      http.post(`${API}/auth/password/reset`, () =>
        HttpResponse.json({ detail: 'The link is invalid or has expired' }, { status: 400 }),
      ),
    )
    renderApp('/reset-password?token=old-token-1234')
    await fill('New password', 'another-long-password')
    await fill('Confirm new password', 'another-long-password')
    await userEvent.click(screen.getByRole('button', { name: 'Change password' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })
})

describe('route guards', () => {
  const guarded = [
    {
      element: <RequireAuth />,
      children: [{ path: '/private', element: <p>secret page</p> }],
    },
    { path: '/login', element: <p>login page</p> },
  ]

  it('sends anonymous visitors to login and remembers where they were going', async () => {
    useSession.setState({ status: 'anonymous', accessToken: null, user: null })
    const router = createMemoryRouter(guarded, { initialEntries: ['/private?tab=1'] })
    render(<RouterProvider router={router} />)
    expect(await screen.findByText('login page')).toBeInTheDocument()
    expect(router.state.location.search).toBe('?next=%2Fprivate%3Ftab%3D1')
    expect(screen.queryByText('secret page')).not.toBeInTheDocument()
  })

  it('shows a loading state, not the page, while the session is being restored', () => {
    render(
      <RouterProvider router={createMemoryRouter(guarded, { initialEntries: ['/private'] })} />,
    )
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
    expect(screen.queryByText('secret page')).not.toBeInTheDocument()
  })

  it('lets signed-in users through', async () => {
    useSession.setState({ status: 'authenticated', accessToken: 't', user: ME })
    render(
      <RouterProvider router={createMemoryRouter(guarded, { initialEntries: ['/private'] })} />,
    )
    expect(await screen.findByText('secret page')).toBeInTheDocument()
  })
})

describe('session restore and sign out', () => {
  it('restores a session from the refresh cookie', async () => {
    server.use(
      http.post(`${API}/auth/refresh`, () => HttpResponse.json(TOKEN)),
      http.get(`${API}/auth/me`, () => HttpResponse.json(ME)),
    )
    await restoreSession()
    expect(useSession.getState()).toMatchObject({ status: 'authenticated', accessToken: 'tok-1' })
  })

  it('becomes anonymous when there is no valid cookie', async () => {
    server.use(
      http.post(`${API}/auth/refresh`, () =>
        HttpResponse.json({ detail: 'Invalid session' }, { status: 401 }),
      ),
    )
    await restoreSession()
    expect(useSession.getState()).toMatchObject({
      status: 'anonymous',
      accessToken: null,
      user: null,
    })
  })

  it('restores only once even if called twice (refresh tokens rotate)', async () => {
    let refreshes = 0
    server.use(
      http.post(`${API}/auth/refresh`, () => {
        refreshes += 1
        return HttpResponse.json(TOKEN)
      }),
      http.get(`${API}/auth/me`, () => HttpResponse.json(ME)),
    )
    await Promise.all([restoreSession(), restoreSession()])
    expect(refreshes).toBe(1)
  })

  it('signing out calls the API with the CSRF header, clears everything and goes to login', async () => {
    let csrf: string | null = null
    server.use(
      http.post(`${API}/auth/logout`, ({ request }) => {
        csrf = request.headers.get('X-Qorvexa-Client')
        return new HttpResponse(null, { status: 204 })
      }),
    )
    useSession.setState({ status: 'authenticated', accessToken: 'tok', user: ME })
    const { router, queryClient } = renderApp('/')
    queryClient.setQueryData(['private'], { secret: true })
    await userEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(csrf).toBe('web')
    expect(useSession.getState()).toMatchObject({
      status: 'anonymous',
      accessToken: null,
      user: null,
    })
    expect(queryClient.getQueryData(['private'])).toBeUndefined()
  })

  it('still signs out locally when the logout request fails', async () => {
    server.use(http.post(`${API}/auth/logout`, () => HttpResponse.error()))
    useSession.setState({ status: 'authenticated', accessToken: 'tok', user: ME })
    renderApp('/')
    await userEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(useSession.getState().status).toBe('anonymous'))
  })
})
