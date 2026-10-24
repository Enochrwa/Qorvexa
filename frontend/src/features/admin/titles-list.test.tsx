import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { adminItem, EDITOR } from '@/test/fixtures'
import { renderApp, signInAs } from '@/test/render'
import { API, server } from '@/test/server'

type Seen = URL[]
function list(items: ReturnType<typeof adminItem>[], total = items.length, seen: Seen = []) {
  return http.get(`${API}/admin/titles`, ({ request }) => {
    seen.push(new URL(request.url))
    return HttpResponse.json({ items, total })
  })
}

describe('studio titles list', () => {
  it('lists titles with a text state, rating and link to the editor', async () => {
    server.use(
      list([
        adminItem(1, { state: 'live', status: 'published' }),
        adminItem(2, { state: 'scheduled', status: 'published', maturity_rating: 'all' }),
        adminItem(3, { type: 'series', state: 'expired' }),
      ]),
    )
    signInAs(EDITOR)
    renderApp('/admin/titles')
    const table = await screen.findByRole('table', { name: 'Titles' })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(4)
    expect(within(rows[1]!).getByRole('link', { name: 'Title 1' })).toHaveAttribute(
      'href',
      expect.stringMatching(/^\/admin\/titles\/0b1f6a52/),
    )
    expect(within(rows[1]!).getByText('live')).toBeInTheDocument()
    expect(within(rows[2]!).getByText('All ages')).toBeInTheDocument()
    expect(within(rows[3]!).getByText('series')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'New title' })).toHaveAttribute(
      'href',
      '/admin/titles/new',
    )
    expect(screen.getByText('Showing 1 to 3 of 3')).toBeInTheDocument()
  })

  it('asks for the first page with no filters by default', async () => {
    const seen: Seen = []
    server.use(list([adminItem(1)], 1, seen))
    signInAs(EDITOR)
    renderApp('/admin/titles')
    await screen.findByRole('table')
    const q = seen[0]!.searchParams
    expect([q.get('limit'), q.get('offset'), q.get('status'), q.get('q')]).toEqual([
      '25',
      '0',
      null,
      null,
    ])
  })

  it('filters by status through the URL', async () => {
    const seen: Seen = []
    server.use(list([adminItem(1)], 1, seen))
    signInAs(EDITOR)
    const { router } = renderApp('/admin/titles')
    await screen.findByRole('table')
    await userEvent.selectOptions(screen.getByLabelText('Status'), 'published')
    await waitFor(() => expect(router.state.location.search).toBe('?status=published'))
    await waitFor(() => expect(seen.at(-1)!.searchParams.get('status')).toBe('published'))
  })

  it('searches after a pause and returns to the first page', async () => {
    const seen: Seen = []
    server.use(list([adminItem(1)], 60, seen))
    signInAs(EDITOR)
    const { router } = renderApp('/admin/titles?page=2')
    await screen.findByRole('table')
    expect(seen[0]!.searchParams.get('offset')).toBe('50')
    await userEvent.type(screen.getByLabelText('Search by name'), 'road')
    await waitFor(() => expect(router.state.location.search).toBe('?q=road'))
    await waitFor(() => expect(seen.at(-1)!.searchParams.get('q')).toBe('road'))
    expect(seen.at(-1)!.searchParams.get('offset')).toBe('0')
    expect(seen.filter((u) => u.searchParams.get('q') === 'r')).toHaveLength(0) // not one request per keystroke
  })

  it('pages with offsets and disables the ends', async () => {
    const seen: Seen = []
    server.use(
      list(
        Array.from({ length: 25 }, (_, i) => adminItem(i + 1)),
        60,
        seen,
      ),
    )
    signInAs(EDITOR)
    const { router } = renderApp('/admin/titles')
    await screen.findByText('Showing 1 to 25 of 60')
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(router.state.location.search).toBe('?page=1'))
    await waitFor(() => expect(seen.at(-1)!.searchParams.get('offset')).toBe('25'))
    await screen.findByText('Showing 26 to 50 of 60')
    await userEvent.click(screen.getByRole('button', { name: 'Previous' }))
    await waitFor(() => expect(router.state.location.search).toBe(''))
  })

  it('ignores hostile URL parameters', async () => {
    const seen: Seen = []
    server.use(list([adminItem(1)], 1, seen))
    signInAs(EDITOR)
    renderApp('/admin/titles?status=deleted&page=-5&q=' + 'x'.repeat(300))
    await screen.findByRole('table')
    const q = seen[0]!.searchParams
    expect(q.get('status')).toBeNull()
    expect(q.get('offset')).toBe('0')
    expect(q.get('q')!.length).toBeLessThanOrEqual(100)
  })

  it('has clear empty states', async () => {
    server.use(list([], 0))
    signInAs(EDITOR)
    const first = renderApp('/admin/titles')
    expect(await screen.findByText('No titles yet. Create the first one.')).toBeInTheDocument()
    first.unmount()
    renderApp('/admin/titles?status=archived')
    expect(await screen.findByText('No titles match.')).toBeInTheDocument()
  })

  it('shows an error and recovers on retry', async () => {
    let fail = true
    server.use(
      http.get(`${API}/admin/titles`, () =>
        fail
          ? HttpResponse.json({ detail: 'x' }, { status: 500 })
          : HttpResponse.json({ items: [adminItem(1)], total: 1 }),
      ),
    )
    signInAs(EDITOR)
    renderApp('/admin/titles')
    expect(await screen.findByRole('alert')).toHaveTextContent('could not load the titles')
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('has no accessibility violations', async () => {
    server.use(list([adminItem(1, { state: 'live' }), adminItem(2)]))
    signInAs(EDITOR)
    const { container } = renderApp('/admin/titles')
    await screen.findByRole('table')
    expect(await axeViolations(container)).toEqual([])
  })
})
