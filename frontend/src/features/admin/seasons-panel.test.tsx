import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { ADMIN_TITLE, EDITOR, TITLE_ID } from '@/test/fixtures'
import { renderApp, signInAs } from '@/test/render'
import { API, server } from '@/test/server'

type Ep = {
  id: string
  number: number
  name: string
  synopsis: string | null
  runtime_seconds: number | null
  air_date: string | null
  intro_start: number | null
  intro_end: number | null
  recap_end: number | null
  status: string
}
type Season = {
  id: string
  title_id: string
  number: number
  name: string | null
  synopsis: string | null
  episodes: Ep[]
}

const ep = (id: string, number: number, name: string, over: Partial<Ep> = {}): Ep => ({
  id,
  number,
  name,
  synopsis: null,
  runtime_seconds: null,
  air_date: null,
  intro_start: null,
  intro_end: null,
  recap_end: null,
  status: 'draft',
  ...over,
})

/** A small stateful fake of the admin seasons/episodes API. */
function fakeApi(initial: Season[]) {
  const state = {
    seasons: structuredClone(initial),
    calls: [] as Array<{ what: string; body?: unknown }>,
    reorderDelay: 0,
    failReorder: false,
    createEpisodeError: null as null | { status: number; detail: string },
  }
  let counter = 100
  const findEp = (id: string) => state.seasons.flatMap((s) => s.episodes).find((e) => e.id === id)
  const handlers = [
    http.get(`${API}/admin/titles/${TITLE_ID}`, () =>
      HttpResponse.json({ ...ADMIN_TITLE, type: 'series' }),
    ),
    http.get(`${API}/admin/titles/${TITLE_ID}/seasons`, () => HttpResponse.json(state.seasons)),
    http.post(`${API}/admin/titles/${TITLE_ID}/seasons`, async ({ request }) => {
      const body = (await request.json()) as {
        number: number
        name: string | null
        synopsis: string | null
      }
      state.calls.push({ what: 'createSeason', body })
      if (state.seasons.some((s) => s.number === body.number))
        return HttpResponse.json({ detail: 'That season number already exists' }, { status: 409 })
      const s: Season = { id: `s${++counter}`, title_id: TITLE_ID, episodes: [], ...body }
      state.seasons.push(s)
      return HttpResponse.json(s, { status: 201 })
    }),
    http.patch(`${API}/admin/seasons/:id`, async ({ request, params }) => {
      const body = (await request.json()) as Partial<Season>
      state.calls.push({ what: 'patchSeason', body })
      const s = state.seasons.find((x) => x.id === params.id)!
      Object.assign(s, body)
      return HttpResponse.json(s)
    }),
    http.delete(`${API}/admin/seasons/:id`, ({ params }) => {
      state.calls.push({ what: 'deleteSeason' })
      state.seasons = state.seasons.filter((s) => s.id !== params.id)
      return new HttpResponse(null, { status: 204 })
    }),
    http.post(`${API}/admin/seasons/:id/episodes`, async ({ request, params }) => {
      const body = (await request.json()) as Omit<Ep, 'id'>
      state.calls.push({ what: 'createEpisode', body })
      if (state.createEpisodeError)
        return HttpResponse.json(
          { detail: state.createEpisodeError.detail },
          { status: state.createEpisodeError.status },
        )
      const s = state.seasons.find((x) => x.id === params.id)!
      if (s.episodes.some((e) => e.number === body.number))
        return HttpResponse.json(
          { detail: 'That episode number already exists in this season' },
          { status: 409 },
        )
      const e = { id: `e${++counter}`, ...body }
      s.episodes.push(e)
      s.episodes.sort((a, b) => a.number - b.number)
      return HttpResponse.json(e, { status: 201 })
    }),
    http.patch(`${API}/admin/episodes/:id`, async ({ request, params }) => {
      const body = (await request.json()) as Partial<Ep>
      state.calls.push({ what: 'patchEpisode', body })
      const e = findEp(params.id as string)!
      Object.assign(e, body)
      return HttpResponse.json(e)
    }),
    http.delete(`${API}/admin/episodes/:id`, ({ params }) => {
      state.calls.push({ what: 'deleteEpisode' })
      for (const s of state.seasons) s.episodes = s.episodes.filter((e) => e.id !== params.id)
      return new HttpResponse(null, { status: 204 })
    }),
    http.post(`${API}/admin/seasons/:id/episodes/reorder`, async ({ request, params }) => {
      const { episode_ids } = (await request.json()) as { episode_ids: string[] }
      state.calls.push({ what: 'reorder', body: episode_ids })
      if (state.reorderDelay) await delay(state.reorderDelay)
      if (state.failReorder) return HttpResponse.json({ detail: 'x' }, { status: 500 })
      const s = state.seasons.find((x) => x.id === params.id)!
      s.episodes = episode_ids.map((id, i) => ({
        ...s.episodes.find((e) => e.id === id)!,
        number: i + 1,
      }))
      return HttpResponse.json(s.episodes)
    }),
  ]
  return { state, handlers }
}

const S1: Season = {
  id: 's1',
  title_id: TITLE_ID,
  number: 1,
  name: 'First',
  synopsis: null,
  episodes: [
    ep('e1', 1, 'Pilot', {
      status: 'published',
      runtime_seconds: 2745,
      synopsis: 'It begins.',
      air_date: '2026-01-02',
      intro_start: 5,
      intro_end: 40,
    }),
    ep('e2', 2, 'Second', { status: 'published', runtime_seconds: 3900 }),
    ep('e3', 3, 'Third'),
  ],
}
const S2: Season = {
  id: 's2',
  title_id: TITLE_ID,
  number: 2,
  name: null,
  synopsis: null,
  episodes: [],
}

async function open(seasons: Season[] = [S1, S2]) {
  const fake = fakeApi(seasons)
  server.use(
    ...fake.handlers,
    http.get(`${API}/genres`, () => HttpResponse.json([])),
  )
  signInAs(EDITOR)
  const utils = renderApp(`/admin/titles/${TITLE_ID}`)
  await screen.findByRole('heading', { name: 'Seasons and episodes' })
  if (seasons.length > 0) await screen.findAllByRole('article') // wait for the data, not just the heading
  return { ...fake, ...utils }
}
const season = (name: string) => within(screen.getByRole('article', { name }))
const names = (s: ReturnType<typeof season>) =>
  s.getAllByRole('listitem').map((li) =>
    within(li)
      .getByText(/(Pilot|Second|Third|Fourth)$/)
      .textContent?.replace(/^Episode \d+: /, ''),
  )

describe('seasons panel visibility and states', () => {
  it('is not shown for movies', async () => {
    server.use(
      http.get(`${API}/admin/titles/${TITLE_ID}`, () => HttpResponse.json(ADMIN_TITLE)),
      http.get(`${API}/genres`, () => HttpResponse.json([])),
    )
    signInAs(EDITOR)
    renderApp(`/admin/titles/${TITLE_ID}`)
    await screen.findByRole('heading', { name: 'Publishing' })
    expect(screen.queryByRole('heading', { name: 'Seasons and episodes' })).not.toBeInTheDocument()
  })

  it('says what to do when there are no seasons', async () => {
    await open([])
    expect(await screen.findByText(/No seasons yet/)).toBeInTheDocument()
  })

  it('shows an error and recovers', async () => {
    let fail = true
    const fake = fakeApi([S1])
    server.use(
      http.get(`${API}/admin/titles/${TITLE_ID}/seasons`, () =>
        fail
          ? HttpResponse.json({ detail: 'x' }, { status: 500 })
          : HttpResponse.json(fake.state.seasons),
      ),
      ...fake.handlers.filter((_h, i) => i !== 1),
      http.get(`${API}/genres`, () => HttpResponse.json([])),
    )
    signInAs(EDITOR)
    renderApp(`/admin/titles/${TITLE_ID}`)
    expect(await screen.findByText('We could not load the seasons.')).toBeInTheDocument()
    fail = false
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('article', { name: 'Season 1: First' })).toBeInTheDocument()
  })

  it('lists seasons and episodes with state and runtime', async () => {
    await open()
    const s1 = season('Season 1: First')
    expect(names(s1)).toEqual(['Pilot', 'Second', 'Third'])
    expect(s1.getByText('Published · 46 min')).toBeInTheDocument()
    expect(s1.getByText('Published · 1 h 5 min')).toBeInTheDocument()
    expect(s1.getByText('Draft')).toBeInTheDocument()
    expect(season('Season 2').getByText('No episodes yet.')).toBeInTheDocument()
  })
})

describe('seasons', () => {
  it('adds a season with the next number', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add season' }))
    expect(screen.getByLabelText('Season number')).toHaveValue('3')
    await userEvent.type(screen.getByLabelText('Season name (optional)'), 'Third season')
    await userEvent.click(screen.getByRole('button', { name: 'Create season' }))
    expect(
      await screen.findByRole('article', { name: 'Season 3: Third season' }),
    ).toBeInTheDocument()
    expect(state.calls.find((c) => c.what === 'createSeason')!.body).toEqual({
      number: 3,
      name: 'Third season',
      synopsis: null,
    })
  })

  it('explains a duplicate number and validates input', async () => {
    await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add season' }))
    await userEvent.clear(screen.getByLabelText('Season number'))
    await userEvent.type(screen.getByLabelText('Season number'), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Create season' }))
    expect(await screen.findByText('That season number is already used.')).toBeInTheDocument()
    await userEvent.clear(screen.getByLabelText('Season number'))
    await userEvent.type(screen.getByLabelText('Season number'), '101')
    await userEvent.click(screen.getByRole('button', { name: 'Create season' }))
    expect(await screen.findByText('Enter a number from 0 to 100')).toBeInTheDocument()
  })

  it('edits a season and sends blank optional fields as null', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Edit Season 1: First' }))
    expect(screen.getByLabelText('Season name (optional)')).toHaveValue('First')
    await userEvent.clear(screen.getByLabelText('Season name (optional)'))
    await userEvent.click(screen.getByRole('button', { name: 'Save season' }))
    await screen.findByRole('article', { name: 'Season 1' })
    expect(state.calls.find((c) => c.what === 'patchSeason')!.body).toEqual({
      number: 1,
      name: null,
      synopsis: null,
    })
  })

  it('asks before deleting a season and says its episodes go too', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Delete Season 2' }))
    const group = screen.getByRole('group', { name: 'Confirm deleting Season 2' })
    expect(group).toHaveTextContent('all its episodes')
    await userEvent.click(within(group).getByRole('button', { name: 'Cancel' }))
    expect(state.calls.some((c) => c.what === 'deleteSeason')).toBe(false)
    await userEvent.click(screen.getByRole('button', { name: 'Delete Season 2' }))
    await userEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    await waitFor(() =>
      expect(screen.queryByRole('article', { name: 'Season 2' })).not.toBeInTheDocument(),
    )
  })
})

describe('episodes', () => {
  it('adds an episode: next number, minutes and seconds become seconds, skip markers and publish flag', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add episode to Season 1: First' }))
    expect(screen.getByLabelText('Episode number')).toHaveValue('4')
    await userEvent.type(screen.getByLabelText('Episode name'), 'Fourth')
    await userEvent.type(screen.getByLabelText('Runtime minutes'), '42')
    await userEvent.type(screen.getByLabelText('Runtime seconds'), '30')
    await userEvent.type(screen.getByLabelText('Intro starts at'), '10')
    await userEvent.type(screen.getByLabelText('Intro ends at'), '55')
    await userEvent.click(screen.getByLabelText('Published (viewers can see this episode)'))
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    await screen.findByText('Published · 43 min') // 42 min 30 s is shown rounded to minutes
    expect(state.calls.find((c) => c.what === 'createEpisode')!.body).toEqual({
      number: 4,
      name: 'Fourth',
      synopsis: null,
      runtime_seconds: 2550,
      air_date: null,
      intro_start: 10,
      intro_end: 55,
      recap_end: null,
      status: 'published',
    })
  })

  it('validates before calling the API', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add episode to Season 2' }))
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    expect(await screen.findByText('Enter a name')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Episode name'), 'X')
    await userEvent.type(screen.getByLabelText('Runtime minutes'), '1')
    await userEvent.type(screen.getByLabelText('Intro starts at'), '50')
    await userEvent.type(screen.getByLabelText('Intro ends at'), '20')
    await userEvent.type(screen.getByLabelText('Recap ends at'), '999')
    await userEvent.type(screen.getByLabelText('Runtime seconds'), '75')
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    expect(await screen.findByText('The intro cannot end before it starts')).toBeInTheDocument()
    expect(screen.getByText('Use 0 to 59')).toBeInTheDocument()
    expect(state.calls.some((c) => c.what === 'createEpisode')).toBe(false)
  })

  it('rejects markers later than the runtime', async () => {
    await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add episode to Season 2' }))
    await userEvent.type(screen.getByLabelText('Episode name'), 'Short')
    await userEvent.type(screen.getByLabelText('Runtime minutes'), '1')
    await userEvent.type(screen.getByLabelText('Recap ends at'), '500')
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    expect(await screen.findByText('Cannot be later than the runtime')).toBeInTheDocument()
  })

  it('explains duplicate numbers and shows other server messages', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Add episode to Season 1: First' }))
    await userEvent.clear(screen.getByLabelText('Episode number'))
    await userEvent.type(screen.getByLabelText('Episode number'), '1')
    await userEvent.type(screen.getByLabelText('Episode name'), 'Dup')
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    expect(
      await screen.findByText('That episode number is already used in this season.'),
    ).toBeInTheDocument()
    state.createEpisodeError = { status: 422, detail: 'intro_end must not exceed runtime_seconds' }
    await userEvent.clear(screen.getByLabelText('Episode number'))
    await userEvent.type(screen.getByLabelText('Episode number'), '9')
    await userEvent.click(screen.getByRole('button', { name: 'Create episode' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'intro_end must not exceed runtime_seconds',
    )
  })

  it('edits an episode with exact runtime prefilled and clears fields with null', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Edit Pilot' }))
    expect(screen.getByLabelText('Runtime minutes')).toHaveValue('45')
    expect(screen.getByLabelText('Runtime seconds')).toHaveValue('45') // 2745 s is not a whole number of minutes
    expect(screen.getByLabelText('Air date')).toHaveValue('2026-01-02')
    expect(screen.getByLabelText('Published (viewers can see this episode)')).toBeChecked()
    await userEvent.clear(screen.getByLabelText('Episode synopsis (optional)'))
    await userEvent.clear(screen.getByLabelText('Intro ends at'))
    await userEvent.clear(screen.getByLabelText('Intro starts at'))
    await userEvent.click(screen.getByRole('button', { name: 'Save episode' }))
    await waitFor(() => expect(state.calls.some((c) => c.what === 'patchEpisode')).toBe(true))
    expect(state.calls.find((c) => c.what === 'patchEpisode')!.body).toMatchObject({
      number: 1,
      name: 'Pilot',
      synopsis: null,
      runtime_seconds: 2745,
      intro_start: null,
      intro_end: null,
      status: 'published',
    })
  })

  it('publishes and unpublishes with one click', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Publish Third' }))
    expect(await screen.findByRole('button', { name: 'Unpublish Third' })).toBeInTheDocument()
    expect(state.calls.at(-1)).toEqual({ what: 'patchEpisode', body: { status: 'published' } })
    await userEvent.click(screen.getByRole('button', { name: 'Unpublish Pilot' }))
    expect(await screen.findByRole('button', { name: 'Publish Pilot' })).toBeInTheDocument()
  })

  it('asks before deleting an episode', async () => {
    const { state } = await open()
    await userEvent.click(screen.getByRole('button', { name: 'Delete Third' }))
    expect(state.calls.some((c) => c.what === 'deleteEpisode')).toBe(false)
    await userEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    await waitFor(() => expect(screen.queryByText('Third')).not.toBeInTheDocument())
  })
})

describe('reordering episodes', () => {
  it('moves an episode down and up, sending the complete new order', async () => {
    const { state } = await open()
    const s1 = season('Season 1: First')
    await userEvent.click(s1.getByRole('button', { name: 'Move Pilot down' }))
    await waitFor(() => expect(names(s1)).toEqual(['Second', 'Pilot', 'Third']))
    expect(state.calls.find((c) => c.what === 'reorder')!.body).toEqual(['e2', 'e1', 'e3'])
    await userEvent.click(s1.getByRole('button', { name: 'Move Third up' }))
    await waitFor(() => expect(names(s1)).toEqual(['Second', 'Third', 'Pilot']))
    expect(state.calls.filter((c) => c.what === 'reorder').at(-1)!.body).toEqual(['e2', 'e3', 'e1'])
  })

  it('announces the move to screen readers', async () => {
    await open()
    await userEvent.click(
      season('Season 1: First').getByRole('button', { name: 'Move Pilot down' }),
    )
    await waitFor(() =>
      expect(screen.getByText('Moved Pilot down to position 2 of 3.')).toBeInTheDocument(),
    )
  })

  it('marks the ends as unavailable without making a request', async () => {
    const { state } = await open()
    const s1 = season('Season 1: First')
    const up = s1.getByRole('button', { name: 'Move Pilot up' })
    const down = s1.getByRole('button', { name: 'Move Third down' })
    expect(up).toHaveAttribute('aria-disabled', 'true')
    expect(down).toHaveAttribute('aria-disabled', 'true')
    await userEvent.click(up)
    await userEvent.click(down)
    expect(state.calls.some((c) => c.what === 'reorder')).toBe(false)
  })

  it('works from the keyboard and keeps focus on the control that was used', async () => {
    await open()
    const s1 = season('Season 1: First')
    s1.getByRole('button', { name: 'Move Pilot down' }).focus()
    await userEvent.keyboard('{Enter}')
    await waitFor(() => expect(names(s1)).toEqual(['Second', 'Pilot', 'Third']))
    expect(s1.getByRole('button', { name: 'Move Pilot down' })).toHaveFocus()
    await userEvent.keyboard('{Enter}') // keep going: Pilot is now last
    await waitFor(() => expect(names(s1)).toEqual(['Second', 'Third', 'Pilot']))
    expect(s1.getByRole('button', { name: 'Move Pilot down' })).toHaveFocus() // still focusable at the end
    expect(s1.getByRole('button', { name: 'Move Pilot down' })).toHaveAttribute(
      'aria-disabled',
      'true',
    )
  })

  it('ignores clicks while a move is in flight', async () => {
    const { state } = await open()
    state.reorderDelay = 150
    const s1 = season('Season 1: First')
    await userEvent.click(s1.getByRole('button', { name: 'Move Pilot down' }))
    await userEvent.click(s1.getByRole('button', { name: 'Move Third up' })) // while busy
    await waitFor(() => expect(names(s1)).toEqual(['Second', 'Pilot', 'Third']))
    expect(state.calls.filter((c) => c.what === 'reorder')).toHaveLength(1)
  })

  it('keeps the old order and reports failure', async () => {
    const { state } = await open()
    state.failReorder = true
    const s1 = season('Season 1: First')
    await userEvent.click(s1.getByRole('button', { name: 'Move Pilot down' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong')
    expect(names(s1)).toEqual(['Pilot', 'Second', 'Third'])
  })
})

it('has no accessibility violations (list, add season form, add episode form)', async () => {
  const { container } = await open()
  expect(await axeViolations(container)).toEqual([])
  await userEvent.click(screen.getByRole('button', { name: 'Add season' }))
  await userEvent.click(screen.getByRole('button', { name: 'Add episode to Season 2' }))
  expect(await axeViolations(container)).toEqual([])
})
