import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { useProfile } from '@/features/profiles/store'
import { axeViolations } from '@/test/axe'
import { GENRES, item } from '@/test/fixtures'
import { renderApp, signIn } from '@/test/render'
import { API, server } from '@/test/server'
import { listTitles } from './api'

type Seen = { url: URL; profile: string | null }
function catalog(
  pages: Array<{ items: ReturnType<typeof item>[]; next_cursor: string | null }>,
  seen: Seen[] = [],
) {
  return [
    http.get(`${API}/genres`, () => HttpResponse.json(GENRES)),
    http.get(`${API}/titles`, ({ request }) => {
      const url = new URL(request.url)
      seen.push({ url, profile: request.headers.get('X-Profile-Id') })
      const cursor = url.searchParams.get('cursor')
      const index = cursor ? Number(cursor.replace('c', '')) : 0
      return HttpResponse.json(pages[index] ?? { items: [], next_cursor: null })
    }),
  ]
}

describe('browse page', () => {
  it('shows skeletons, then linked cards with year and rating', async () => {
    server.use(
      ...catalog([
        {
          items: [item(1), item(2, { maturity_rating: 'all', release_year: null })],
          next_cursor: null,
        },
      ]),
    )
    renderApp('/browse')
    expect(screen.getByRole('status', { name: 'Loading titles' })).toBeInTheDocument()
    const link = await screen.findByRole('link', { name: /Title 1/ })
    expect(link).toHaveAttribute('href', '/titles/title-1')
    expect(link).toHaveTextContent('2021 · 13+')
    expect(screen.getByRole('link', { name: /Title 2/ })).toHaveTextContent('All ages')
    expect(screen.getByText('Showing 2 titles')).toBeInTheDocument()
  })

  it('sends sane defaults and no profile header when anonymous', async () => {
    const seen: Seen[] = []
    server.use(...catalog([{ items: [item(1)], next_cursor: null }], seen))
    renderApp('/browse')
    await screen.findByRole('link', { name: /Title 1/ })
    const q = seen[0]!.url.searchParams
    expect([q.get('sort'), q.get('limit'), q.get('type'), q.get('genre'), q.get('cursor')]).toEqual(
      ['added', '24', null, null, null],
    )
    expect(seen[0]!.profile).toBeNull()
  })

  it('filters through the URL and the request', async () => {
    const seen: Seen[] = []
    server.use(...catalog([{ items: [item(1)], next_cursor: null }], seen))
    const { router } = renderApp('/browse')
    await screen.findByRole('link', { name: /Title 1/ })
    await userEvent.selectOptions(screen.getByLabelText('Type'), 'series')
    await userEvent.selectOptions(
      await screen
        .findByRole('option', { name: 'Drama' })
        .then(() => screen.getByLabelText('Genre')),
      'drama',
    )
    await userEvent.selectOptions(screen.getByLabelText('Sort by'), 'name')
    await waitFor(() =>
      expect(router.state.location.search).toBe('?type=series&genre=drama&sort=name'),
    )
    await waitFor(() => {
      const q = seen[seen.length - 1]!.url.searchParams
      expect([q.get('type'), q.get('genre'), q.get('sort')]).toEqual(['series', 'drama', 'name'])
    })
    await userEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    await waitFor(() => expect(router.state.location.search).toBe('?sort=name'))
  })

  it('opens a deep link with the filters already applied', async () => {
    const seen: Seen[] = []
    server.use(...catalog([{ items: [item(1)], next_cursor: null }], seen))
    renderApp('/browse?type=movie&genre=drama&sort=year')
    await screen.findByRole('link', { name: /Title 1/ })
    expect(screen.getByLabelText('Type')).toHaveValue('movie')
    expect(screen.getByLabelText('Genre')).toHaveValue('drama')
    expect(screen.getByLabelText('Sort by')).toHaveValue('year')
    expect(seen[0]!.url.searchParams.get('genre')).toBe('drama')
  })

  it('ignores hostile or invalid URL parameters', async () => {
    const seen: Seen[] = []
    server.use(...catalog([{ items: [item(1)], next_cursor: null }], seen))
    renderApp('/browse?type=book&genre=Bad%20Slug!&sort=popular&cursor=evil')
    await screen.findByRole('link', { name: /Title 1/ })
    const q = seen[0]!.url.searchParams
    expect([q.get('type'), q.get('genre'), q.get('sort'), q.get('cursor')]).toEqual([
      null,
      null,
      'added',
      null,
    ])
  })

  it('loads more with the cursor, appends, and hides the button at the end', async () => {
    const seen: Seen[] = []
    server.use(
      ...catalog(
        [
          { items: [item(1), item(2)], next_cursor: 'c1' },
          { items: [item(3)], next_cursor: null },
        ],
        seen,
      ),
    )
    renderApp('/browse')
    await userEvent.click(await screen.findByRole('button', { name: 'Load more' }))
    expect(await screen.findByRole('link', { name: /Title 3/ })).toBeInTheDocument()
    expect(seen[1]!.url.searchParams.get('cursor')).toBe('c1')
    expect(screen.getAllByRole('link', { name: /Title \d/ })).toHaveLength(3)
    expect(screen.getByText('Showing 3 titles')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
  })

  it('keeps what is shown when loading more fails', async () => {
    let calls = 0
    server.use(
      http.get(`${API}/genres`, () => HttpResponse.json(GENRES)),
      http.get(`${API}/titles`, () => {
        calls += 1
        return calls === 1
          ? HttpResponse.json({ items: [item(1)], next_cursor: 'c1' })
          : HttpResponse.json({ detail: 'x' }, { status: 500 })
      }),
    )
    renderApp('/browse')
    await userEvent.click(await screen.findByRole('button', { name: 'Load more' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('could not load more')
    expect(screen.getByRole('link', { name: /Title 1/ })).toBeInTheDocument()
  })

  it('shows an empty state with a way out when filters match nothing', async () => {
    server.use(...catalog([{ items: [], next_cursor: null }]))
    renderApp('/browse?type=series')
    expect(await screen.findByText('No titles match these filters.')).toBeInTheDocument()
    await userEvent.click(screen.getAllByRole('button', { name: 'Clear filters' })[0]!)
    await waitFor(() => expect(screen.getByLabelText('Type')).toHaveValue(''))
  })

  it('shows an error and recovers on retry', async () => {
    let fail = true
    server.use(
      http.get(`${API}/genres`, () => HttpResponse.json(GENRES)),
      http.get(`${API}/titles`, () =>
        fail
          ? HttpResponse.json({ detail: 'x' }, { status: 500 })
          : HttpResponse.json({ items: [item(1)], next_cursor: null }),
      ),
    )
    renderApp('/browse')
    expect(await screen.findByRole('alert')).toHaveTextContent('could not load the titles')
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('link', { name: /Title 1/ })).toBeInTheDocument()
  })

  it('renders posters only over https and falls back when an image fails', async () => {
    server.use(
      ...catalog([
        {
          items: [
            item(1, { poster_url: 'https://img.example.com/ok.jpg' }),
            item(2, { poster_url: 'http://img.example.com/insecure.jpg' }),
            item(3, { poster_url: 'javascript:alert(1)' }),
          ],
          next_cursor: null,
        },
      ]),
    )
    const { container } = renderApp('/browse')
    await screen.findByRole('link', { name: /Title 1/ })
    const imgs = container.querySelectorAll('img')
    expect(imgs).toHaveLength(1)
    expect(imgs[0]).toHaveAttribute('src', 'https://img.example.com/ok.jpg')
    expect(imgs[0]).toHaveAttribute('width', '300') // reserves space: no layout shift
    expect(imgs[0]).toHaveAttribute('loading', 'lazy')
    fireEvent.error(imgs[0]!)
    await waitFor(() => expect(container.querySelectorAll('img')).toHaveLength(0))
  })

  it('has no accessibility violations (results, empty, error)', async () => {
    server.use(...catalog([{ items: [item(1), item(2)], next_cursor: 'c1' }]))
    const ok = renderApp('/browse')
    await screen.findByRole('link', { name: /Title 1/ })
    expect(await axeViolations(ok.container)).toEqual([])
    ok.unmount()
    server.use(http.get(`${API}/titles`, () => HttpResponse.json({ items: [], next_cursor: null })))
    const empty = renderApp('/browse')
    await screen.findByText('No titles match these filters.')
    expect(await axeViolations(empty.container)).toEqual([])
    empty.unmount()
    server.use(http.get(`${API}/titles`, () => HttpResponse.json({ detail: 'x' }, { status: 500 })))
    const err = renderApp('/browse')
    await screen.findByRole('alert')
    expect(await axeViolations(err.container)).toEqual([])
  })

  it('redirects the home page to browse', async () => {
    server.use(...catalog([{ items: [item(1)], next_cursor: null }]))
    const { router } = renderApp('/')
    await waitFor(() => expect(router.state.location.pathname).toBe('/browse'))
  })
})

describe('browse with profiles', () => {
  it('sends the selected profile and re-fetches when it changes', async () => {
    const seen: Seen[] = []
    server.use(...catalog([{ items: [item(1)], next_cursor: null }], seen))
    signIn()
    useProfile.setState({ selectedId: 'p1' })
    renderApp('/browse')
    await screen.findByRole('link', { name: /Title 1/ })
    expect(seen[0]!.profile).toBe('p1')
    act(() => useProfile.setState({ selectedId: 'p2' }))
    await waitFor(() => expect(seen.at(-1)!.profile).toBe('p2')) // different audience, different cache entry
  })

  it('recovers when the selected profile was deleted elsewhere', async () => {
    const profiles: Array<string | null> = []
    server.use(
      http.get(`${API}/titles`, ({ request }) => {
        const header = request.headers.get('X-Profile-Id')
        profiles.push(header)
        return header
          ? HttpResponse.json({ detail: 'Profile not found' }, { status: 404 })
          : HttpResponse.json({ items: [item(1)], next_cursor: null })
      }),
    )
    signIn()
    useProfile.setState({ selectedId: 'gone' })
    const result = await listTitles({ type: null, genre: null, sort: 'added' }, null)
    expect(result.items).toHaveLength(1)
    expect(profiles).toEqual(['gone', null]) // one failed attempt, one retry without the stale profile
    expect(useProfile.getState().selectedId).toBeNull()
  })

  it('does not retry forever or hide other 404s', async () => {
    let calls = 0
    server.use(
      http.get(`${API}/titles`, () => {
        calls += 1
        return HttpResponse.json({ detail: 'Profile not found' }, { status: 404 })
      }),
    )
    signIn()
    useProfile.setState({ selectedId: 'gone' })
    await expect(
      listTitles({ type: null, genre: null, sort: 'added' }, null),
    ).rejects.toMatchObject({ status: 404 })
    expect(calls).toBe(2) // original + exactly one retry
  })
})

it('the filter form is labelled and its controls are reachable by keyboard', async () => {
  server.use(...catalog([{ items: [item(1)], next_cursor: null }]))
  renderApp('/browse')
  const form = await screen.findByRole('form', { name: 'Filter titles' })
  const selects = within(form).getAllByRole('combobox')
  expect(
    selects.map((s) => (s as HTMLSelectElement).labels?.[0]?.textContent?.trim().split('\n')[0]),
  ).toEqual(
    expect.arrayContaining([
      expect.stringContaining('Type'),
      expect.stringContaining('Genre'),
      expect.stringContaining('Sort by'),
    ]),
  )
})
