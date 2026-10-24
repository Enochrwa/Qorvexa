import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { ADMIN_USER, EDITOR, ME } from '@/test/fixtures'
import { renderApp, signInAs } from '@/test/render'
import { API, server } from '@/test/server'
import { hasRole } from './role'

describe('hasRole', () => {
  it('ranks viewer < editor < admin and rejects missing users', () => {
    expect(hasRole(ME, 'viewer')).toBe(true)
    expect(hasRole(ME, 'editor')).toBe(false)
    expect(hasRole(EDITOR, 'editor')).toBe(true)
    expect(hasRole(EDITOR, 'admin')).toBe(false)
    expect(hasRole(ADMIN_USER, 'editor')).toBe(true)
    expect(hasRole(null, 'viewer')).toBe(false)
    expect(hasRole({ ...ME, role: 'superuser' }, 'viewer')).toBe(false) // unknown roles get nothing
  })
})

describe('studio access', () => {
  it('sends anonymous visitors to sign in and brings them back', async () => {
    const { router } = renderApp('/admin/titles')
    await screen.findByRole('heading', { name: 'Sign in' })
    expect(router.state.location.search).toBe('?next=%2Fadmin%2Ftitles')
  })

  it('shows viewers an explanation and makes no admin requests', async () => {
    let adminCalls = 0
    server.use(
      http.get(`${API}/admin/titles`, () => {
        adminCalls += 1
        return HttpResponse.json({ items: [], total: 0 })
      }),
    )
    signInAs(ME)
    renderApp('/admin/titles')
    expect(
      await screen.findByRole('heading', { name: /do not have access to the studio/i }),
    ).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Titles' })).not.toBeInTheDocument()
    expect(adminCalls).toBe(0)
  })

  it.each([
    ['editor', EDITOR],
    ['admin', ADMIN_USER],
  ])('lets an %s in', async (_role, user) => {
    server.use(http.get(`${API}/admin/titles`, () => HttpResponse.json({ items: [], total: 0 })))
    signInAs(user)
    renderApp('/admin/titles')
    expect(await screen.findByRole('heading', { name: 'Titles' })).toBeInTheDocument()
    await screen.findByText('No titles yet. Create the first one.') // wait for its request to finish
  })

  it('shows the Studio link in the header only to editors and admins', async () => {
    signInAs(ME)
    const viewer = renderApp('/browse')
    await screen.findByRole('heading', { name: 'Browse' })
    expect(screen.queryByRole('link', { name: 'Studio' })).not.toBeInTheDocument()
    viewer.unmount()
    signInAs(EDITOR)
    renderApp('/browse')
    expect(await screen.findByRole('link', { name: 'Studio' })).toHaveAttribute('href', '/admin')
  })

  it('redirects /admin to the titles list', async () => {
    server.use(http.get(`${API}/admin/titles`, () => HttpResponse.json({ items: [], total: 0 })))
    signInAs(EDITOR)
    const { router } = renderApp('/admin')
    await waitFor(() => expect(router.state.location.pathname).toBe('/admin/titles'))
    await screen.findByRole('heading', { name: 'Titles' }) // let the lazy page finish loading
  })
})
