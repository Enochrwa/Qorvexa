import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { StrictMode } from 'react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { routes } from '@/app/router'
import { useSession } from '@/lib/api/session'

/**
 * Render the real routes. The session starts as anonymous (as it would after a failed restore)
 * unless the test already set one; pass `strict` to render under React StrictMode.
 */
export function renderApp(path: string, options: { strict?: boolean } = {}) {
  if (useSession.getState().status === 'loading') {
    useSession.setState({ status: 'anonymous', accessToken: null, user: null })
  }
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const tree = (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
  const utils = render(options.strict ? <StrictMode>{tree}</StrictMode> : tree)
  return { ...utils, router, queryClient }
}

export const ME = { id: 'u1', email: 'viewer@example.com', role: 'viewer', email_verified: true }
