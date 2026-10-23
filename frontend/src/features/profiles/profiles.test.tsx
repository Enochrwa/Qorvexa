import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { axeViolations } from '@/test/axe'
import { PROFILES, renderApp, signIn } from '@/test/render'
import { API, server } from '@/test/server'
import { useProfile } from './store'

const list = (profiles = PROFILES) => http.get(`${API}/profiles`, () => HttpResponse.json(profiles))
const extra = (n: number) =>
  Array.from({ length: n }, (_, i) => ({ ...PROFILES[0]!, id: `x${i}`, name: `Extra ${i}` }))

describe('profile picker', () => {
  it('requires a signed-in user', async () => {
    renderApp('/profiles')
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument(),
    )
  })

  it('lists profiles, remembers the choice per account and goes to the requested page', async () => {
    server.use(list())
    signIn()
    const { router } = renderApp('/profiles?next=%2Fprofiles%2Fmanage')
    await userEvent.click(await screen.findByRole('button', { name: /Kids/ }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/profiles/manage'))
    expect(useProfile.getState().selectedId).toBe('p2')
    expect(localStorage.getItem('qorvexa.profile.u1')).toBe('p2')
  })

  it('never redirects to another site from ?next', async () => {
    server.use(list())
    signIn()
    const { router } = renderApp('/profiles?next=https%3A%2F%2Fevil.example.com')
    await userEvent.click(await screen.findByRole('button', { name: /Alex/ }))
    await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  })

  it('shows an error instead of an empty picker when loading fails', async () => {
    server.use(
      http.get(`${API}/profiles`, () => HttpResponse.json({ detail: 'x' }, { status: 500 })),
    )
    signIn()
    renderApp('/profiles')
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load your profiles/i)
  })

  it('has no accessibility violations', async () => {
    server.use(list())
    signIn()
    const { container } = renderApp('/profiles')
    await screen.findByRole('button', { name: /Alex/ })
    expect(await axeViolations(container)).toEqual([])
  })
})

describe('selected profile in the header and requests', () => {
  it('shows the chosen profile and sends X-Profile-Id on catalog requests only', async () => {
    const seen: Record<string, string | null> = {}
    server.use(
      list(),
      http.get(`${API}/titles`, ({ request }) => {
        seen.titles = request.headers.get('X-Profile-Id')
        return HttpResponse.json({ items: [], next_cursor: null })
      }),
    )
    signIn()
    localStorage.setItem('qorvexa.profile.u1', 'p2')
    useProfile.getState().hydrate('u1')
    renderApp('/')
    expect(await screen.findByRole('link', { name: /Kids · Switch profile/ })).toHaveAttribute(
      'href',
      '/profiles',
    )
    const { api } = await import('@/lib/api/client')
    await api.GET('/api/v1/titles')
    expect(seen.titles).toBe('p2')
  })

  it('does not send the profile header to auth or profile endpoints', async () => {
    let header: string | null = 'unset'
    server.use(
      http.get(`${API}/profiles`, ({ request }) => {
        header = request.headers.get('X-Profile-Id')
        return HttpResponse.json(PROFILES)
      }),
    )
    signIn()
    useProfile.setState({ selectedId: 'p1' })
    const { listProfiles } = await import('./api')
    await listProfiles()
    expect(header).toBeNull()
  })

  it('never sends a profile header without a signed-in token', async () => {
    let header: string | null = 'unset'
    server.use(
      http.get(`${API}/titles`, ({ request }) => {
        header = request.headers.get('X-Profile-Id')
        return HttpResponse.json({ items: [], next_cursor: null })
      }),
    )
    useProfile.setState({ selectedId: 'p1' })
    const { api } = await import('@/lib/api/client')
    await api.GET('/api/v1/titles')
    expect(header).toBeNull()
  })

  it('forgets a remembered profile that no longer exists', async () => {
    server.use(list())
    signIn()
    localStorage.setItem('qorvexa.profile.u1', 'deleted-elsewhere')
    useProfile.getState().hydrate('u1')
    renderApp('/')
    await waitFor(() => expect(useProfile.getState().selectedId).toBeNull())
    expect(localStorage.getItem('qorvexa.profile.u1')).toBeNull()
  })

  it('selects a lone profile automatically', async () => {
    server.use(list([PROFILES[0]!]))
    signIn()
    renderApp('/')
    await waitFor(() => expect(useProfile.getState().selectedId).toBe('p1'))
  })

  it("does not use another account's remembered profile", () => {
    localStorage.setItem('qorvexa.profile.someone-else', 'p2')
    useProfile.getState().hydrate('u1')
    expect(useProfile.getState().selectedId).toBeNull()
  })

  it('survives blocked storage', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(() => useProfile.getState().hydrate('u1')).not.toThrow()
    spy.mockRestore()
  })
})

describe('manage profiles', () => {
  it('creates a profile with the chosen options', async () => {
    let body: Record<string, unknown> = {}
    server.use(
      list(),
      http.post(`${API}/profiles`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...PROFILES[1], id: 'p3', name: 'Teen' }, { status: 201 })
      }),
    )
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Add profile' }))
    await userEvent.type(screen.getByLabelText('Name'), '  Teen ')
    await userEvent.click(screen.getByRole('radio', { name: 'Avatar 7' }))
    await userEvent.selectOptions(screen.getByLabelText('Maturity limit'), '13+')
    await userEvent.selectOptions(screen.getByLabelText('Language'), 'rw')
    await userEvent.click(screen.getByLabelText('Data saver (lower video quality)'))
    await userEvent.click(screen.getByLabelText('Show subtitles by default'))
    await userEvent.click(screen.getByRole('button', { name: 'Create profile' }))
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Manage profiles' })).toBeInTheDocument(),
    )
    expect(body).toMatchObject({
      name: 'Teen',
      avatar: 'avatar-7',
      language: 'rw',
      maturity_limit: '13+',
      data_saver: true,
      autoplay_next: true,
      subtitle_prefs: { enabled: true, size: 'medium' },
    })
  })

  it('validates the name before calling the API', async () => {
    server.use(list())
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Add profile' }))
    await userEvent.click(screen.getByRole('button', { name: 'Create profile' }))
    expect(await screen.findByText('Enter a name')).toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toHaveFocus()
  })

  it.each([
    [
      'duplicate name',
      'You already have a profile with that name',
      'You already have a profile with that name.',
    ],
    [
      'limit',
      'An account can have at most 5 profiles',
      'You have reached the maximum number of profiles.',
    ],
  ])('explains a 409 (%s)', async (_n, detail, message) => {
    server.use(
      list(),
      http.post(`${API}/profiles`, () => HttpResponse.json({ detail }, { status: 409 })),
    )
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Add profile' }))
    await userEvent.type(screen.getByLabelText('Name'), 'Alex')
    await userEvent.click(screen.getByRole('button', { name: 'Create profile' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
  })

  it('edits an existing profile with its current values prefilled', async () => {
    let body: Record<string, unknown> = {}
    server.use(
      list(),
      http.patch(`${API}/profiles/p2`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...PROFILES[1], name: 'Little Kids' })
      }),
    )
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Kids' }))
    expect(screen.getByLabelText('Name')).toHaveValue('Kids')
    expect(screen.getByLabelText('Maturity limit')).toHaveValue('7+')
    expect(screen.getByLabelText('Language')).toHaveValue('rw')
    expect(screen.getByLabelText('Subtitle size')).toHaveValue('large')
    expect(screen.getByLabelText('Show subtitles by default')).toBeChecked()
    await userEvent.clear(screen.getByLabelText('Name'))
    await userEvent.type(screen.getByLabelText('Name'), 'Little Kids')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(body).toMatchObject({ name: 'Little Kids', maturity_limit: '7+' }))
  })

  it('cancel leaves everything unchanged', async () => {
    server.use(list())
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Kids' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(await screen.findByRole('heading', { name: 'Manage profiles' })).toBeInTheDocument()
  })

  it('asks for confirmation before deleting, and forgets a deleted selection', async () => {
    let deleted = 0
    server.use(
      list(),
      http.delete(`${API}/profiles/p2`, () => {
        deleted += 1
        return new HttpResponse(null, { status: 204 })
      }),
    )
    signIn()
    useProfile.setState({ selectedId: 'p2' })
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Delete Kids' }))
    expect(deleted).toBe(0)
    const confirm = screen.getByRole('group', { name: 'Confirm deleting Kids' })
    await userEvent.click(within(confirm).getByRole('button', { name: 'Cancel' }))
    expect(deleted).toBe(0)
    await userEvent.click(screen.getByRole('button', { name: 'Delete Kids' }))
    await userEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    await waitFor(() => expect(deleted).toBe(1))
    await waitFor(() => expect(useProfile.getState().selectedId).toBeNull())
  })

  it('cannot delete the only profile', async () => {
    server.use(list([PROFILES[0]!]))
    signIn()
    renderApp('/profiles/manage')
    expect(await screen.findByRole('button', { name: 'Delete Alex' })).toBeDisabled()
  })

  it('disables adding at the profile limit and says why', async () => {
    server.use(list(extra(5)))
    signIn()
    renderApp('/profiles/manage')
    expect(await screen.findByRole('button', { name: 'Add profile' })).toBeDisabled()
    expect(screen.getByText(/reached the maximum of 5 profiles/i)).toBeInTheDocument()
  })

  it('reports a failed delete without losing the list', async () => {
    server.use(
      list(),
      http.delete(`${API}/profiles/p2`, () => HttpResponse.json({ detail: 'x' }, { status: 500 })),
    )
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Delete Kids' }))
    await userEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong')
    expect(screen.getByRole('button', { name: 'Edit Kids' })).toBeInTheDocument()
  })

  it('has no accessibility violations (list, create form, edit form)', async () => {
    server.use(list())
    signIn()
    const { container } = renderApp('/profiles/manage')
    await screen.findByRole('button', { name: 'Edit Kids' })
    expect(await axeViolations(container)).toEqual([])
    await userEvent.click(screen.getByRole('button', { name: 'Add profile' }))
    expect(await axeViolations(container)).toEqual([])
  })

  it('the avatar picker is a keyboard-operable radio group', async () => {
    server.use(list())
    signIn()
    renderApp('/profiles/manage')
    await userEvent.click(await screen.findByRole('button', { name: 'Add profile' }))
    const group = screen.getByRole('group', { name: 'Avatar' })
    expect(within(group).getAllByRole('radio')).toHaveLength(12)
    within(group).getByRole('radio', { name: 'Avatar 1' }).focus()
    await userEvent.keyboard('{ArrowRight}')
    expect(within(group).getByRole('radio', { name: 'Avatar 2' })).toBeChecked()
  })
})

describe('sign out', () => {
  it('forgets the in-memory profile but keeps the remembered choice for the next sign in', async () => {
    server.use(
      list(),
      http.post(`${API}/auth/logout`, () => new HttpResponse(null, { status: 204 })),
    )
    signIn()
    localStorage.setItem('qorvexa.profile.u1', 'p2')
    useProfile.getState().hydrate('u1')
    renderApp('/')
    await userEvent.click(await screen.findByRole('button', { name: 'Sign out' }))
    await waitFor(() => expect(useProfile.getState().selectedId).toBeNull())
    expect(localStorage.getItem('qorvexa.profile.u1')).toBe('p2')
  })
})
