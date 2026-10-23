import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { type Filters } from './api'
import { useGenres, useTitles } from './hooks'
import { parseFilters, toSearchParams } from './params'
import { TitleCard, TitleCardSkeleton } from './TitleCard'

const selectClass = 'h-11 rounded-md border border-surface-3 bg-surface-1 px-3 text-text'

export function BrowsePage() {
  const [params, setParams] = useSearchParams()
  const filters = parseFilters(params)
  const genres = useGenres()
  const titles = useTitles(filters)

  useEffect(() => {
    document.title = 'Browse · Qorvexa'
  }, [])

  const update = (patch: Partial<Filters>) => setParams(toSearchParams({ ...filters, ...patch }))
  const items = titles.data?.pages.flatMap((p) => p.items) ?? []
  const filtered = filters.type !== null || filters.genre !== null
  const genreOptions = genres.data ?? []
  const unknownGenre = filters.genre && !genreOptions.some((g) => g.slug === filters.genre)

  return (
    <section className="flex flex-col gap-6">
      <h1 className="text-3xl font-semibold">Browse</h1>

      <form
        aria-label="Filter titles"
        onSubmit={(e) => e.preventDefault()}
        className="flex flex-wrap items-end gap-4"
      >
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Type
          <select
            className={selectClass}
            value={filters.type ?? ''}
            onChange={(e) =>
              update({ type: e.target.value === '' ? null : (e.target.value as Filters['type']) })
            }
          >
            <option value="">All</option>
            <option value="movie">Movies</option>
            <option value="series">Series</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Genre
          <select
            className={selectClass}
            value={filters.genre ?? ''}
            onChange={(e) => update({ genre: e.target.value || null })}
          >
            <option value="">All genres</option>
            {unknownGenre && filters.genre ? (
              <option value={filters.genre}>{filters.genre}</option>
            ) : null}
            {genreOptions.map((g) => (
              <option key={g.slug} value={g.slug}>
                {g.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Sort by
          <select
            className={selectClass}
            value={filters.sort}
            onChange={(e) => update({ sort: e.target.value as Filters['sort'] })}
          >
            <option value="added">Recently added</option>
            <option value="name">Name (A to Z)</option>
            <option value="year">Newest release</option>
          </select>
        </label>
        {filtered ? (
          <Button type="button" variant="ghost" onClick={() => update({ type: null, genre: null })}>
            Clear filters
          </Button>
        ) : null}
      </form>

      {titles.isPending ? (
        <div role="status" aria-label="Loading titles">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {Array.from({ length: 12 }, (_, i) => (
              <TitleCardSkeleton key={i} />
            ))}
          </div>
        </div>
      ) : titles.isError && !titles.data ? (
        <div role="alert" className="flex flex-col items-start gap-3 text-danger">
          <p>We could not load the titles. Please try again.</p>
          <Button variant="secondary" onClick={() => void titles.refetch()}>
            Try again
          </Button>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-start gap-3">
          <p role="status">No titles match these filters.</p>
          {filtered ? (
            <Button variant="secondary" onClick={() => update({ type: null, genre: null })}>
              Clear filters
            </Button>
          ) : null}
        </div>
      ) : (
        <>
          <p role="status" className="text-sm text-text-muted">
            Showing {items.length} {items.length === 1 ? 'title' : 'titles'}
          </p>
          <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {items.map((t) => (
              <li key={t.id}>
                <TitleCard title={t} />
              </li>
            ))}
          </ul>
          {titles.hasNextPage ? (
            <div>
              <Button
                variant="secondary"
                onClick={() => void titles.fetchNextPage()}
                disabled={titles.isFetchingNextPage}
              >
                {titles.isFetchingNextPage ? 'Loading…' : 'Load more'}
              </Button>
            </div>
          ) : null}
          {titles.isFetchNextPageError ? (
            <p role="alert" className="text-danger">
              We could not load more titles. Try again.
            </p>
          ) : null}
        </>
      )}
    </section>
  )
}
