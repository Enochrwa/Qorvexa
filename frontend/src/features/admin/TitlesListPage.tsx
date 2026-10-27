import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import { adminKey, listAdminTitles, PAGE } from './api'
import { StateBadge } from './StateBadge'

const STATUSES = ['draft', 'published', 'archived'] as const
const fieldClass = 'h-11 rounded-md border border-surface-3 bg-surface-1 px-3 text-text'

export function TitlesListPage() {
  const [params, setParams] = useSearchParams()
  const status = STATUSES.find((s) => s === params.get('status')) ?? null
  const q = (params.get('q') ?? '').slice(0, 100) || null
  const page = Math.max(0, Math.min(Number(params.get('page')) || 0, 4000))
  const [draft, setDraft] = useState(q ?? '')

  useEffect(() => {
    document.title = 'Titles · Studio · Qorvexa'
  }, [])

  // Search as you type, but only after a short pause, and always from the first page.
  useEffect(() => {
    if (draft.trim() === (q ?? '')) return
    const t = setTimeout(() => {
      const next = new URLSearchParams(params)
      if (draft.trim()) next.set('q', draft.trim())
      else next.delete('q')
      next.delete('page')
      setParams(next, { replace: true })
    }, 300)
    return () => clearTimeout(t)
  }, [draft, q, params, setParams])

  const query = useQuery({
    queryKey: [...adminKey, { status, q, page }],
    queryFn: () => listAdminTitles({ status, q, offset: page * PAGE }),
    placeholderData: keepPreviousData,
  })

  const set = (key: string, value: string | null) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  const data = query.data
  const first = data && data.total > 0 ? page * PAGE + 1 : 0
  const last = data ? Math.min(data.total, page * PAGE + data.items.length) : 0

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-2xl font-semibold">Titles</h2>
        <Link
          to="/admin/titles/new"
          className="inline-flex h-11 items-center rounded-md bg-accent-solid px-4 font-medium text-white hover:bg-accent-solid-hover"
        >
          New title
        </Link>
      </div>

      <form
        role="search"
        aria-label="Find titles"
        onSubmit={(e) => e.preventDefault()}
        className="flex flex-wrap gap-4"
      >
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Search by name
          <input
            type="search"
            className={fieldClass}
            value={draft}
            maxLength={100}
            onChange={(e) => setDraft(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Status
          <select
            className={fieldClass}
            value={status ?? ''}
            onChange={(e) => set('status', e.target.value || null)}
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s[0]?.toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </form>

      {query.isPending ? (
        <div role="status" aria-label="Loading titles" className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : query.isError && !data ? (
        <div role="alert" className="flex flex-col items-start gap-3 text-danger">
          <p>We could not load the titles.</p>
          <Button variant="secondary" onClick={() => void query.refetch()}>
            Try again
          </Button>
        </div>
      ) : data && data.items.length === 0 ? (
        <p role="status">
          {q || status ? 'No titles match.' : 'No titles yet. Create the first one.'}
        </p>
      ) : data ? (
        <>
          <div className="overflow-x-auto rounded-lg border border-surface-2">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Titles</caption>
              <thead className="bg-surface-1 text-text-muted">
                <tr>
                  <th scope="col" className="p-3">
                    Name
                  </th>
                  <th scope="col" className="p-3">
                    Type
                  </th>
                  <th scope="col" className="p-3">
                    State
                  </th>
                  <th scope="col" className="p-3">
                    Rating
                  </th>
                  <th scope="col" className="p-3">
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((t) => (
                  <tr key={t.id} className="border-t border-surface-2">
                    <th scope="row" className="p-3 font-medium">
                      <Link to={`/admin/titles/${t.id}`} className="text-accent underline">
                        {t.name}
                      </Link>
                    </th>
                    <td className="p-3 capitalize">{t.type}</td>
                    <td className="p-3">
                      <StateBadge state={t.state} />
                    </td>
                    <td className="p-3">
                      {t.maturity_rating === 'all' ? 'All ages' : t.maturity_rating}
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {new Date(t.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav aria-label="Pages" className="flex items-center gap-3">
            <Button
              size="sm"
              variant="secondary"
              disabled={page === 0}
              onClick={() => set('page', page - 1 > 0 ? String(page - 1) : null)}
            >
              Previous
            </Button>
            <p role="status" className="text-sm text-text-muted">
              {`Showing ${first} to ${last} of ${data.total}`}
            </p>
            <Button
              size="sm"
              variant="secondary"
              disabled={last >= data.total}
              onClick={() => set('page', String(page + 1))}
            >
              Next
            </Button>
          </nav>
        </>
      ) : null}
    </section>
  )
}
