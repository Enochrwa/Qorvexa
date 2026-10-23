import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { DETAIL, GENRES, SEASONS } from '@/test/fixtures'
import { renderApp } from '@/test/render'
import { API, server } from '@/test/server'

const movie = () => http.get(`${API}/titles/the-long-road`, () => HttpResponse.json(DETAIL))
const series = () =>
  http.get(`${API}/titles/the-long-road`, () =>
    HttpResponse.json({ ...DETAIL, type: 'series', season_count: 2 }),
  )
const seasons = (body: object = SEASONS) =>
  http.get(`${API}/titles/the-long-road/seasons`, () => HttpResponse.json(body))

describe('title detail', () => {
  it('shows a movie with metadata, genres, synopsis and credits', async () => {
    server.use(
      movie(),
      http.get(`${API}/genres`, () => HttpResponse.json(GENRES)),
    )
    renderApp('/titles/the-long-road')
    expect(
      await screen.findByRole('heading', { level: 1, name: 'The Long Road' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Rated 13+')).toBeInTheDocument()
    expect(screen.getByText('2021')).toBeInTheDocument()
    expect(screen.getByText('Movie')).toBeInTheDocument()
    expect(screen.getByText('EN')).toBeInTheDocument()
    expect(screen.getByText('A journey across the country.')).toBeInTheDocument()
    expect(
      within(screen.getByRole('list', { name: 'Genres' })).getByRole('link', { name: 'Drama' }),
    ).toHaveAttribute('href', '/browse?genre=drama')
    expect(screen.getByText('Directed by').nextSibling).toHaveTextContent('Dee Rector')
    expect(screen.getByText('Starring').nextSibling).toHaveTextContent('Amy Lead, Zed Actor')
    expect(screen.queryByRole('heading', { name: 'Episodes' })).not.toBeInTheDocument()
    expect(document.title).toBe('The Long Road · Qorvexa')
  })

  it('does not request seasons for a movie', async () => {
    let asked = false
    server.use(
      movie(),
      http.get(`${API}/titles/the-long-road/seasons`, () => {
        asked = true
        return HttpResponse.json([])
      }),
    )
    renderApp('/titles/the-long-road')
    await screen.findByRole('heading', { level: 1 })
    expect(asked).toBe(false)
  })

  it('lists a series season by season with formatted runtimes', async () => {
    server.use(series(), seasons())
    renderApp('/titles/the-long-road')
    expect(await screen.findByRole('heading', { name: 'Episodes' })).toBeInTheDocument()
    const first = await screen.findByRole('heading', { level: 3, name: /Pilot/ })
    expect(first).toHaveTextContent('Episode 1: Pilot')
    expect(first).toHaveTextContent('45 min')
    expect(screen.getByRole('heading', { level: 3, name: /Second/ })).toHaveTextContent('1 h 5 min')
    expect(screen.getByText('It begins.')).toBeInTheDocument()
    const group = screen.getByRole('group', { name: 'Seasons' })
    expect(within(group).getByRole('button', { name: 'First' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await userEvent.click(within(group).getByRole('button', { name: 'Season 2' }))
    expect(within(group).getByRole('button', { name: 'Season 2' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(await screen.findByRole('heading', { level: 3, name: /Return/ })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { level: 3, name: /Pilot/ })).not.toBeInTheDocument()
  })

  it('says so when a series has no published episodes yet', async () => {
    server.use(series(), seasons([]))
    renderApp('/titles/the-long-road')
    expect(await screen.findByText('No episodes have been published yet.')).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Seasons' })).not.toBeInTheDocument()
  })

  it('handles a season with no published episodes', async () => {
    server.use(series(), seasons([{ number: 1, name: null, synopsis: null, episodes: [] }]))
    renderApp('/titles/the-long-road')
    expect(
      await screen.findByText(/no episodes have been published for this season/i),
    ).toBeInTheDocument()
  })

  it('shows a calm "not available" page for a hidden or missing title, without retrying', async () => {
    let calls = 0
    server.use(
      http.get(`${API}/titles/the-long-road`, () => {
        calls += 1
        return HttpResponse.json({ detail: 'Title not found' }, { status: 404 })
      }),
    )
    renderApp('/titles/the-long-road')
    expect(
      await screen.findByRole('heading', { name: 'This title is not available' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to browse' })).toHaveAttribute('href', '/browse')
    expect(calls).toBe(1)
  })

  it('rejects a malformed slug without calling the API', async () => {
    renderApp('/titles/Not%20A%20Slug!')
    expect(
      await screen.findByRole('heading', { name: 'This title is not available' }),
    ).toBeInTheDocument()
  })

  it('shows a retryable error for server failures', async () => {
    let fail = true
    server.use(
      http.get(`${API}/titles/the-long-road`, () =>
        fail ? HttpResponse.json({ detail: 'x' }, { status: 500 }) : HttpResponse.json(DETAIL),
      ),
    )
    renderApp('/titles/the-long-road')
    expect(await screen.findByRole('alert')).toHaveTextContent('could not load this title')
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(
      await screen.findByRole('heading', { level: 1, name: 'The Long Road' }),
    ).toBeInTheDocument()
  })

  it('keeps the page when only the episodes fail to load', async () => {
    server.use(
      series(),
      http.get(`${API}/titles/the-long-road/seasons`, () =>
        HttpResponse.json({ detail: 'x' }, { status: 500 }),
      ),
    )
    renderApp('/titles/the-long-road')
    expect(
      await screen.findByRole('heading', { level: 1, name: 'The Long Road' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('We could not load the episodes.')).toBeInTheDocument()
  })

  it('only uses https backdrops and posters', async () => {
    server.use(
      http.get(`${API}/titles/the-long-road`, () =>
        HttpResponse.json({
          ...DETAIL,
          backdrop_url: 'http://x.example.com/b.jpg',
          poster_url: 'javascript:alert(1)',
        }),
      ),
    )
    const { container } = renderApp('/titles/the-long-road')
    await screen.findByRole('heading', { level: 1 })
    expect(container.querySelectorAll('img')).toHaveLength(0)
  })

  it('has no accessibility violations (movie and series)', async () => {
    server.use(movie())
    const m = renderApp('/titles/the-long-road')
    await screen.findByRole('heading', { level: 1, name: 'The Long Road' })
    expect(await axeViolations(m.container)).toEqual([])
    m.unmount()
    server.use(series(), seasons())
    const s = renderApp('/titles/the-long-road')
    await screen.findByRole('heading', { level: 3, name: /Pilot/ })
    expect(await axeViolations(s.container)).toEqual([])
  })

  it('links back from a genre chip to a filtered browse page', async () => {
    server.use(
      movie(),
      http.get(`${API}/genres`, () => HttpResponse.json(GENRES)),
      http.get(`${API}/titles`, () => HttpResponse.json({ items: [], next_cursor: null })),
    )
    const { router } = renderApp('/titles/the-long-road')
    await userEvent.click(await screen.findByRole('link', { name: 'Drama' }))
    await waitFor(() => expect(router.state.location.search).toBe('?genre=drama'))
  })
})
