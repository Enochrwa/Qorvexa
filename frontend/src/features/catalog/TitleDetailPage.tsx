import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import { ApiError } from '@/lib/api/errors'
import { useSeasons, useTitle } from './hooks'
import { formatRuntime, ratingLabel, safeImageUrl } from './params'
import { Poster } from './Poster'

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/
const ROLE_LABEL: Record<string, string> = {
  director: 'Directed by',
  actor: 'Starring',
  writer: 'Written by',
}

function NotAvailable() {
  return (
    <section className="flex flex-col items-start gap-3 py-8">
      <h1 className="text-2xl font-semibold">This title is not available</h1>
      <p className="text-text-muted">
        It may have been removed or is not available for your profile.
      </p>
      <Link to="/browse" className="text-accent underline">
        Back to browse
      </Link>
    </section>
  )
}

export function TitleDetailPage() {
  const { slug = '' } = useParams()
  if (!SLUG.test(slug)) return <NotAvailable />
  return <Detail slug={slug} />
}

function Detail({ slug }: { slug: string }) {
  const title = useTitle(slug)
  const isSeries = title.data?.type === 'series'
  const seasons = useSeasons(slug, isSeries)
  const [chosen, setChosen] = useState<number | null>(null)

  useEffect(() => {
    document.title = title.data ? `${title.data.name} · Qorvexa` : 'Qorvexa'
  }, [title.data])

  if (title.isPending) {
    return (
      <div role="status" aria-label="Loading title" className="flex flex-col gap-4 py-4">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }
  if (title.error instanceof ApiError && title.error.status === 404) return <NotAvailable />
  if (title.isError) {
    return (
      <div role="alert" className="flex flex-col items-start gap-3 py-8 text-danger">
        <p>We could not load this title. Please try again.</p>
        <Button variant="secondary" onClick={() => void title.refetch()}>
          Try again
        </Button>
      </div>
    )
  }

  const t = title.data
  const backdrop = safeImageUrl(t.backdrop_url)
  const runtimeMeta = [
    t.release_year,
    t.type === 'movie' ? 'Movie' : 'Series',
    t.language ? t.language.toUpperCase() : null,
    t.country,
  ].filter(Boolean)
  const credits = Object.entries(ROLE_LABEL)
    .map(([role, label]) => ({
      label,
      names: t.cast.filter((c) => c.role === role).map((c) => c.name),
    }))
    .filter((c) => c.names.length > 0)
  const seasonList = seasons.data ?? []
  const current = seasonList.find((s) => s.number === chosen) ?? seasonList[0]

  return (
    <article className="flex flex-col gap-8">
      <Link to="/browse" className="text-sm text-accent underline">
        ← Back to browse
      </Link>

      <header className="relative overflow-hidden rounded-lg bg-surface-1">
        {backdrop ? (
          <>
            <img
              src={backdrop}
              alt=""
              width={1280}
              height={720}
              decoding="async"
              className="absolute inset-0 h-full w-full object-cover opacity-40"
            />
            <div
              aria-hidden="true"
              className="absolute inset-0 bg-gradient-to-t from-bg via-bg/70 to-transparent"
            />
          </>
        ) : null}
        <div className="relative flex flex-col gap-6 p-4 sm:flex-row sm:p-8">
          <Poster url={t.poster_url} name={t.name} className="w-40 shrink-0 self-start sm:w-52" />
          <div className="flex flex-col gap-4">
            <h1 className="text-3xl font-bold">{t.name}</h1>
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-text-muted">
              <span className="rounded border border-text-muted px-1.5 py-0.5 text-text">
                {`Rated ${ratingLabel(t.maturity_rating)}`}
              </span>
              {runtimeMeta.map((m) => (
                <span key={String(m)}>{m}</span>
              ))}
            </p>
            {t.genres.length > 0 ? (
              <ul aria-label="Genres" className="flex flex-wrap gap-2">
                {t.genres.map((g) => (
                  <li key={g.slug}>
                    <Link
                      to={`/browse?genre=${g.slug}`}
                      className="rounded-full bg-surface-2 px-3 py-1 text-sm hover:bg-surface-3"
                    >
                      {g.name}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
            {t.synopsis ? <p className="max-w-prose whitespace-pre-line">{t.synopsis}</p> : null}
            {credits.length > 0 ? (
              <dl className="flex flex-col gap-1 text-sm">
                {credits.map((c) => (
                  <div key={c.label} className="flex gap-2">
                    <dt className="text-text-muted">{c.label}</dt>
                    <dd>{c.names.join(', ')}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </div>
        </div>
      </header>

      {isSeries ? (
        <section aria-labelledby="episodes-heading" className="flex flex-col gap-4">
          <h2 id="episodes-heading" className="text-xl font-semibold">
            Episodes
          </h2>
          {seasons.isPending ? (
            <div role="status" aria-label="Loading episodes">
              <Skeleton className="h-24 w-full" />
            </div>
          ) : seasons.isError ? (
            <div role="alert" className="flex flex-col items-start gap-3 text-danger">
              <p>We could not load the episodes.</p>
              <Button variant="secondary" onClick={() => void seasons.refetch()}>
                Try again
              </Button>
            </div>
          ) : !current ? (
            <p className="text-text-muted">No episodes have been published yet.</p>
          ) : (
            <>
              {seasonList.length > 1 ? (
                <div role="group" aria-label="Seasons" className="flex flex-wrap gap-2">
                  {seasonList.map((s) => (
                    <Button
                      key={s.number}
                      size="sm"
                      variant={s.number === current.number ? 'primary' : 'secondary'}
                      aria-pressed={s.number === current.number}
                      onClick={() => setChosen(s.number)}
                    >
                      {s.name ?? `Season ${s.number}`}
                    </Button>
                  ))}
                </div>
              ) : null}
              {current.episodes.length === 0 ? (
                <p className="text-text-muted">
                  No episodes have been published for this season yet.
                </p>
              ) : (
                <ol className="flex flex-col divide-y divide-surface-2 rounded-lg border border-surface-2 bg-surface-1">
                  {current.episodes.map((e) => (
                    <li key={e.id} className="flex gap-4 p-4">
                      <span
                        className="w-8 shrink-0 text-lg font-semibold text-text-muted"
                        aria-hidden="true"
                      >
                        {e.number}
                      </span>
                      <div className="flex flex-col gap-1">
                        <h3 className="font-medium">
                          <span className="sr-only">{`Episode ${e.number}: `}</span>
                          {e.name}
                          {formatRuntime(e.runtime_seconds) ? (
                            <span className="ml-2 text-sm font-normal text-text-muted">
                              {formatRuntime(e.runtime_seconds)}
                            </span>
                          ) : null}
                        </h3>
                        {e.synopsis ? (
                          <p className="text-sm text-text-muted">{e.synopsis}</p>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </>
          )}
        </section>
      ) : null}
    </article>
  )
}
