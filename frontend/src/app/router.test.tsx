import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { renderApp } from '@/test/render'
import { API, server } from '@/test/server'

const empty = () => [
  http.get(`${API}/genres`, () => HttpResponse.json([])),
  http.get(`${API}/titles`, () => HttpResponse.json({ items: [], next_cursor: null })),
]

describe('router', () => {
  it('renders the app shell with the browse page at the home address', async () => {
    server.use(...empty())
    const { router } = renderApp('/')
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
    await waitFor(() => expect(router.state.location.pathname).toBe('/browse'))
    expect(await screen.findByRole('heading', { name: 'Browse' })).toBeInTheDocument()
  })

  it('renders not found for unknown routes', () => {
    renderApp('/nope')
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument()
  })

  it('shows sign in for anonymous visitors only', async () => {
    server.use(...empty())
    renderApp('/browse')
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
    expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument()
    await screen.findByText('No titles match these filters.')
  })
})
