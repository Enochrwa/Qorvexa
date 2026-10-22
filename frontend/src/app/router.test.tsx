import { screen } from '@testing-library/react'
import { renderApp } from '@/test/render'

describe('router', () => {
  it('renders the app shell and home page', () => {
    renderApp('/')
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /welcome to qorvexa/i })).toBeInTheDocument()
  })

  it('renders not found for unknown routes', () => {
    renderApp('/nope')
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument()
  })

  it('shows sign in for anonymous visitors only', () => {
    renderApp('/')
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
    expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument()
  })
})
