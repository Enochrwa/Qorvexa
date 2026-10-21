import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { routes } from './router'

describe('router', () => {
  it('renders the app shell and home page', () => {
    render(<RouterProvider router={createMemoryRouter(routes, { initialEntries: ['/'] })} />)
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /welcome to qorvexa/i })).toBeInTheDocument()
  })

  it('renders not found for unknown routes', () => {
    render(<RouterProvider router={createMemoryRouter(routes, { initialEntries: ['/nope'] })} />)
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument()
  })
})
