import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { renderApp } from '@/test/render'
import { API, server } from '@/test/server'

describe('auth pages have no detectable accessibility violations', () => {
  it.each([
    ['/login', 'Sign in'],
    ['/register', 'Create your account'],
    ['/forgot-password', 'Reset your password'],
    ['/reset-password?token=abc-token-12345', 'Choose a new password'],
    ['/reset-password', 'Choose a new password'],
  ])('%s', async (path, heading) => {
    const { container } = renderApp(path)
    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
    expect(await axeViolations(container)).toEqual([])
  })

  it('verify email (failed and succeeded states)', async () => {
    server.use(http.post(`${API}/auth/verify-email`, () => new HttpResponse(null, { status: 204 })))
    const ok = renderApp('/verify-email?token=verify-token-123')
    expect(await screen.findByText(/your email is verified/i)).toBeInTheDocument()
    expect(await axeViolations(ok.container)).toEqual([])
    ok.unmount()
    const bad = renderApp('/verify-email')
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(await axeViolations(bad.container)).toEqual([])
  })

  it('error state: errors are announced and linked to their field', async () => {
    const { container } = renderApp('/login')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    const email = await screen.findByLabelText('Email')
    expect(email).toHaveAttribute('aria-invalid', 'true')
    expect(email).toHaveAccessibleDescription('Enter your email')
    expect(await axeViolations(container)).toEqual([])
  })

  it('moves keyboard focus to the first invalid field on submit', async () => {
    renderApp('/register')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await screen.findByText('Enter your email')
    expect(screen.getByLabelText('Email')).toHaveFocus()
  })

  it('the form is fully keyboard operable (tab order and Enter to submit)', async () => {
    let body: unknown
    server.use(
      http.post(`${API}/auth/login`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
      }),
    )
    renderApp('/login')
    // The header links come first in the tab order; start at the form's first field.
    screen.getByLabelText('Email').focus()
    await userEvent.keyboard('viewer@example.com')
    await userEvent.tab()
    expect(screen.getByLabelText('Password')).toHaveFocus()
    await userEvent.keyboard('a-long-enough-pass{Enter}')
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(body).toEqual({ email: 'viewer@example.com', password: 'a-long-enough-pass' })
  })
})
