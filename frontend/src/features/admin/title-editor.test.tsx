import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { ADMIN_TITLE, EDITOR, GENRES, TITLE_ID } from '@/test/fixtures'
import { renderApp, signInAs } from '@/test/render'
import { API, server } from '@/test/server'

const genres = () => http.get(`${API}/genres`, () => HttpResponse.json(GENRES))
/** A tiny stateful stand-in for the server: reads return the latest state, writes update it. */
let current: Record<string, unknown> = { ...ADMIN_TITLE }
const get = (over: Record<string, unknown> = {}) => {
  current = { ...ADMIN_TITLE, ...over }
  return http.get(`${API}/admin/titles/${TITLE_ID}`, () => HttpResponse.json(current))
}
const reply = (next: Record<string, unknown>, status = 200) => {
  current = next
  return HttpResponse.json(next, { status })
}
const type = (label: string, text: string) => userEvent.type(screen.getByLabelText(label), text)

describe('create title', () => {
  const open = async () => {
    server.use(
      genres(),
      http.get(`${API}/admin/titles`, () => HttpResponse.json({ items: [], total: 0 })),
    )
    signInAs(EDITOR)
    const utils = renderApp('/admin/titles/new')
    await screen.findByRole('heading', { name: 'New title' })
    return utils
  }

  it('starts at the most restrictive rating and explains it', async () => {
    await open()
    expect(screen.getByLabelText('Maturity rating')).toHaveValue('18+')
    expect(screen.getByText(/start at 18\+ \(most restricted\)/i)).toBeInTheDocument()
  })

  it('validates before calling the API', async () => {
    await open()
    await type('Release year', '19')
    await type('Country (2 letters)', 'r')
    await type('Poster image address (https)', 'http://insecure.example.com/p.jpg')
    await type('Backdrop image address (https)', 'javascript:alert(1)')
    await type('Slug (optional, made from the name)', 'Bad Slug')
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    expect(await screen.findByText('Enter a name')).toBeInTheDocument()
    expect(screen.getByText('Enter a year between 1888 and 2100')).toBeInTheDocument()
    expect(screen.getByText('Use a 2-letter code such as RW')).toBeInTheDocument()
    expect(screen.getAllByText('Use a full https:// address')).toHaveLength(2)
    expect(screen.getByText('Use lowercase letters, numbers and hyphens')).toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toHaveFocus()
  })

  it('rejects duplicate cast entries', async () => {
    await open()
    await type('Name', 'Film')
    for (let i = 0; i < 2; i++)
      await userEvent.click(screen.getByRole('button', { name: 'Add person' }))
    await type('Person 1 name', 'Amy Lead')
    await type('Person 2 name', 'amy lead')
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    expect(await screen.findByText('Each person can appear once per role')).toBeInTheDocument()
  })

  it('sends blank optional fields as null, keeps cast order, and opens the editor', async () => {
    let body: Record<string, unknown> = {}
    server.use(
      http.post(`${API}/admin/titles`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...ADMIN_TITLE }, { status: 201 })
      }),
      get(),
    )
    const { router } = await open()
    await type('Name', '  The Long Road ')
    await userEvent.selectOptions(screen.getByLabelText('Type'), 'series')
    await userEvent.selectOptions(screen.getByLabelText('Maturity rating'), '13+')
    await type('Release year', '2021')
    await type('Poster image address (https)', 'https://img.example.com/p.jpg')
    await userEvent.click(await screen.findByRole('checkbox', { name: 'Drama' }))
    await userEvent.click(screen.getByRole('button', { name: 'Add person' }))
    await userEvent.click(screen.getByRole('button', { name: 'Add person' }))
    await type('Person 1 name', 'Dee Rector')
    await userEvent.selectOptions(screen.getByLabelText('Person 1 role'), 'director')
    await type('Person 2 name', 'Amy Lead')
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    await waitFor(() => expect(router.state.location.pathname).toBe(`/admin/titles/${TITLE_ID}`))
    await screen.findByRole('heading', { level: 2, name: ADMIN_TITLE.name }) // let the editor finish loading
    expect(body).toEqual({
      name: 'The Long Road',
      type: 'series',
      slug: null,
      original_name: null,
      synopsis: null,
      release_year: 2021,
      maturity_rating: '13+',
      language: null,
      country: null,
      poster_url: 'https://img.example.com/p.jpg',
      backdrop_url: null,
      downloads_enabled: false,
      genres: ['drama'],
      cast: [
        { name: 'Dee Rector', role: 'director', billing_order: 0 },
        { name: 'Amy Lead', role: 'actor', billing_order: 1 },
      ],
    })
  })

  it('shows a slug conflict next to the slug field', async () => {
    server.use(
      http.post(`${API}/admin/titles`, () =>
        HttpResponse.json({ detail: 'A title with that slug already exists' }, { status: 409 }),
      ),
    )
    await open()
    await type('Name', 'Film')
    await type('Slug (optional, made from the name)', 'taken')
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    expect(
      await screen.findByText('That slug is already used by another title.'),
    ).toBeInTheDocument()
  })

  it('shows server validation messages and generic failures safely', async () => {
    let status = 422
    server.use(
      http.post(`${API}/admin/titles`, () =>
        status === 422
          ? HttpResponse.json({ detail: 'Unknown genre(s): nope' }, { status: 422 })
          : HttpResponse.json({ detail: 'Traceback: secret internals' }, { status: 500 }),
      ),
    )
    await open()
    await type('Name', 'Film')
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unknown genre(s): nope')
    status = 500
    await userEvent.click(screen.getByRole('button', { name: 'Create title' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong'))
    expect(screen.getByRole('alert')).not.toHaveTextContent(/traceback/i)
  })

  it('counts synopsis characters and has no accessibility violations', async () => {
    const { container } = await open()
    await userEvent.type(screen.getByLabelText('Synopsis'), 'hello')
    expect(screen.getByText('5 of 5000 characters')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Add person' }))
    expect(await axeViolations(container)).toEqual([])
  })
})

describe('edit title', () => {
  const open = async (over: Record<string, unknown> = {}) => {
    server.use(
      genres(),
      get(over),
      http.get(`${API}/admin/titles`, () => HttpResponse.json({ items: [], total: 0 })),
    )
    signInAs(EDITOR)
    const utils = renderApp(`/admin/titles/${TITLE_ID}`)
    await screen.findByRole('heading', { level: 2, name: ADMIN_TITLE.name })
    return utils
  }

  it('prefills every field and locks type and slug', async () => {
    await open()
    expect(screen.getByLabelText('Name')).toHaveValue('The Long Road')
    expect(screen.getByLabelText('Slug (address)')).toHaveAttribute('readonly')
    expect(screen.getByLabelText('Slug (address)')).toHaveValue('the-long-road')
    expect(screen.getByLabelText('Type')).toBeDisabled()
    expect(screen.getByLabelText('Synopsis')).toHaveValue('A journey.')
    expect(screen.getByLabelText('Country (2 letters)')).toHaveValue('RW')
    expect(await screen.findByRole('checkbox', { name: 'Drama' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Comedy' })).not.toBeChecked()
    expect(screen.getByLabelText('Person 1 name')).toHaveValue('Dee Rector')
    expect(screen.getByLabelText('Person 2 role')).toHaveValue('actor')
  })

  it('patches without slug or type, and clears a field with null', async () => {
    let body: Record<string, unknown> = {}
    await open()
    server.use(
      http.patch(`${API}/admin/titles/${TITLE_ID}`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          ...ADMIN_TITLE,
          name: 'Renamed',
          poster_url: null,
          updated_at: '2026-10-22T11:00:00Z',
        })
      }),
    )
    await screen.findByRole('checkbox', { name: 'Drama' })
    await userEvent.clear(screen.getByLabelText('Name'))
    await type('Name', 'Renamed')
    await userEvent.clear(screen.getByLabelText('Poster image address (https)'))
    await userEvent.click(screen.getByRole('button', { name: 'Remove person 2' }))
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByText('Changes saved.')).toBeInTheDocument()
    expect(body).not.toHaveProperty('slug')
    expect(body).not.toHaveProperty('type')
    expect(body).toMatchObject({
      name: 'Renamed',
      poster_url: null,
      genres: ['drama'],
      cast: [{ name: 'Dee Rector', role: 'director', billing_order: 0 }],
    })
  })

  it('shows not-found for unknown and malformed ids', async () => {
    server.use(
      http.get(`${API}/admin/titles/${TITLE_ID}`, () =>
        HttpResponse.json({ detail: 'Title not found' }, { status: 404 }),
      ),
    )
    signInAs(EDITOR)
    const a = renderApp(`/admin/titles/${TITLE_ID}`)
    expect(await screen.findByRole('heading', { name: 'Title not found' })).toBeInTheDocument()
    a.unmount()
    renderApp('/admin/titles/not-a-uuid')
    expect(await screen.findByRole('heading', { name: 'Title not found' })).toBeInTheDocument()
  })

  it('has no accessibility violations', async () => {
    const { container } = await open()
    await screen.findByRole('checkbox', { name: 'Drama' })
    expect(await axeViolations(container)).toEqual([])
  })
})

describe('publishing', () => {
  const open = async (over: Record<string, unknown> = {}) => {
    server.use(
      genres(),
      get(over),
      http.get(`${API}/admin/titles`, () => HttpResponse.json({ items: [], total: 0 })),
    )
    signInAs(EDITOR)
    const utils = renderApp(`/admin/titles/${TITLE_ID}`)
    await screen.findByRole('heading', { name: 'Publishing' })
    return utils
  }
  const panel = () => within(screen.getByRole('region', { name: 'Publishing' }))

  it('explains why a title cannot be published yet', async () => {
    await open()
    server.use(
      http.post(`${API}/admin/titles/${TITLE_ID}/publish`, () =>
        HttpResponse.json(
          { detail: 'Title is not ready to publish: missing synopsis, poster_url' },
          { status: 409 },
        ),
      ),
    )
    await userEvent.click(panel().getByRole('button', { name: 'Publish' }))
    expect(await panel().findByRole('alert')).toHaveTextContent('missing synopsis, poster_url')
    expect(panel().getByText('draft')).toBeInTheDocument()
  })

  it('publishes now, with no times sent', async () => {
    let body: unknown
    await open()
    server.use(
      http.post(`${API}/admin/titles/${TITLE_ID}/publish`, async ({ request }) => {
        body = await request.json()
        return reply({ ...ADMIN_TITLE, status: 'published', state: 'live' })
      }),
    )
    await userEvent.click(panel().getByRole('button', { name: 'Publish' }))
    expect(await panel().findByText('live')).toBeInTheDocument()
    expect(body).toEqual({ publish_at: null, available_until: null })
    expect(panel().getByRole('button', { name: 'Update schedule' })).toBeInTheDocument()
    expect(panel().getByRole('button', { name: 'Unpublish' })).toBeInTheDocument()
  })

  it('sends schedule times as timezone-aware ISO strings and shows the embargo', async () => {
    let body: { publish_at: string; available_until: string } | undefined
    await open()
    server.use(
      http.post(`${API}/admin/titles/${TITLE_ID}/publish`, async ({ request }) => {
        body = (await request.json()) as typeof body
        return reply({
          ...ADMIN_TITLE,
          status: 'published',
          state: 'scheduled',
          publish_at: '2030-01-02T10:30:00Z',
        })
      }),
    )
    fireEvent.change(panel().getByLabelText(/Publish at/), {
      target: { value: '2030-01-02T10:30' },
    })
    fireEvent.change(panel().getByLabelText(/Available until/), {
      target: { value: '2030-06-01T00:00' },
    })
    await userEvent.click(panel().getByRole('button', { name: 'Publish' }))
    expect(await panel().findByText(/Hidden from viewers until/)).toBeInTheDocument()
    expect(body!.publish_at).toBe(new Date('2030-01-02T10:30').toISOString())
    expect(body!.publish_at.endsWith('Z')).toBe(true)
    expect(body!.available_until).toBe(new Date('2030-06-01T00:00').toISOString())
  })

  it('unpublishes', async () => {
    await open({ status: 'published', state: 'live' })
    server.use(
      http.post(`${API}/admin/titles/${TITLE_ID}/unpublish`, () =>
        reply({ ...ADMIN_TITLE, status: 'draft', state: 'draft' }),
      ),
    )
    await userEvent.click(panel().getByRole('button', { name: 'Unpublish' }))
    expect(await panel().findByText('draft')).toBeInTheDocument()
    expect(panel().queryByRole('button', { name: 'Unpublish' })).not.toBeInTheDocument()
  })

  it('will not offer deleting a published title', async () => {
    await open({ status: 'published', state: 'live' })
    expect(panel().getByRole('button', { name: 'Delete title' })).toBeDisabled()
    expect(panel().getByText('Unpublish a title before deleting it.')).toBeInTheDocument()
  })

  it('asks before deleting, then returns to the list', async () => {
    let deleted = 0
    const { router } = await open()
    server.use(
      http.delete(`${API}/admin/titles/${TITLE_ID}`, () => {
        deleted += 1
        return new HttpResponse(null, { status: 204 })
      }),
    )
    await userEvent.click(panel().getByRole('button', { name: 'Delete title' }))
    expect(deleted).toBe(0)
    expect(panel().getByRole('group', { name: 'Confirm deleting this title' })).toHaveTextContent(
      'This cannot be undone',
    )
    await userEvent.click(panel().getByRole('button', { name: 'Cancel' }))
    expect(deleted).toBe(0)
    await userEvent.click(panel().getByRole('button', { name: 'Delete title' }))
    await userEvent.click(panel().getByRole('button', { name: 'Yes, delete' }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/admin/titles'))
    expect(deleted).toBe(1)
  })

  it('reports a refused delete and keeps the title', async () => {
    await open()
    server.use(
      http.delete(`${API}/admin/titles/${TITLE_ID}`, () =>
        HttpResponse.json({ detail: 'Unpublish the title before deleting it' }, { status: 409 }),
      ),
    )
    await userEvent.click(panel().getByRole('button', { name: 'Delete title' }))
    await userEvent.click(panel().getByRole('button', { name: 'Yes, delete' }))
    expect(await panel().findByRole('alert')).toHaveTextContent(
      'Unpublish the title before deleting it',
    )
    expect(screen.getByRole('heading', { level: 2, name: 'The Long Road' })).toBeInTheDocument()
  })
})
