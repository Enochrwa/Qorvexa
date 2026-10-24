import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import { FormAlert } from '@/features/auth/AuthLayout'
import { formatRuntime } from '@/features/catalog/params'
import {
  createAdminEpisode,
  createAdminSeason,
  deleteAdminEpisode,
  deleteAdminSeason,
  listAdminSeasons,
  patchAdminEpisode,
  patchAdminSeason,
  reorderAdminEpisodes,
  seasonsKey,
  type AdminEpisode,
  type AdminSeason,
} from './api'
import { EpisodeForm } from './EpisodeForm'
import { adminMessage } from './messages'
import {
  episodeToBody,
  episodeToForm,
  nextNumber,
  seasonToBody,
  seasonToForm,
} from './season-mapping'
import { SeasonForm } from './SeasonForm'

const moveClass = 'aria-disabled:cursor-not-allowed aria-disabled:opacity-40'

export function SeasonsPanel({ titleId }: { titleId: string }) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: seasonsKey(titleId),
    queryFn: () => listAdminSeasons(titleId),
  })
  const [adding, setAdding] = useState(false)
  const [announcement, setAnnouncement] = useState('')
  const [error, setError] = useState<string | null>(null)
  const refresh = () => queryClient.invalidateQueries({ queryKey: seasonsKey(titleId) })

  return (
    <section aria-labelledby="seasons-heading" className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <h2 id="seasons-heading" className="text-xl font-semibold">
          Seasons and episodes
        </h2>
        {!adding ? (
          <Button size="sm" onClick={() => setAdding(true)}>
            Add season
          </Button>
        ) : null}
      </div>
      <FormAlert message={error} />
      <p role="status" aria-live="polite" className="sr-only">
        {announcement}
      </p>

      {adding ? (
        <SeasonForm
          initial={seasonToForm(
            undefined,
            nextNumber(
              (query.data ?? []).map((s) => s.number),
              1,
            ),
          )}
          submitLabel="Create season"
          onCancel={() => setAdding(false)}
          onSubmit={async (v) => {
            await createAdminSeason(titleId, seasonToBody(v))
            await refresh()
            setAdding(false)
          }}
        />
      ) : null}

      {query.isPending ? (
        <div role="status" aria-label="Loading seasons">
          <Skeleton className="h-24 w-full" />
        </div>
      ) : query.isError ? (
        <div role="alert" className="flex flex-col items-start gap-3 text-danger">
          <p>We could not load the seasons.</p>
          <Button variant="secondary" size="sm" onClick={() => void query.refetch()}>
            Try again
          </Button>
        </div>
      ) : query.data.length === 0 && !adding ? (
        <p className="text-text-muted">
          No seasons yet. Add the first season to start adding episodes.
        </p>
      ) : (
        query.data.map((season) => (
          <SeasonCard
            key={season.id}
            season={season}
            onChanged={refresh}
            onError={setError}
            onAnnounce={setAnnouncement}
            replace={(next) =>
              queryClient.setQueryData<AdminSeason[]>(seasonsKey(titleId), (old) =>
                (old ?? []).map((s) => (s.id === season.id ? { ...s, episodes: next } : s)),
              )
            }
          />
        ))
      )}
    </section>
  )
}

function SeasonCard(props: {
  season: AdminSeason
  onChanged: () => Promise<unknown>
  onError: (m: string | null) => void
  onAnnounce: (m: string) => void
  replace: (episodes: AdminEpisode[]) => void
}) {
  const { season, onChanged, onError, onAnnounce, replace } = props
  const episodes = season.episodes ?? []
  const [editing, setEditing] = useState(false)
  const [confirmSeason, setConfirmSeason] = useState(false)
  const [addingEpisode, setAddingEpisode] = useState(false)
  const [editingEpisode, setEditingEpisode] = useState<string | null>(null)
  const [confirmEpisode, setConfirmEpisode] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const label = season.name ? `Season ${season.number}: ${season.name}` : `Season ${season.number}`

  async function guarded(fn: () => Promise<unknown>) {
    onError(null)
    setBusy(true)
    try {
      await fn()
    } catch (err) {
      setConfirmSeason(false)
      setConfirmEpisode(null)
      onError(adminMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function move(index: number, delta: -1 | 1) {
    const target = index + delta
    if (busy || target < 0 || target >= episodes.length) return
    const ids = episodes.map((e) => e.id)
    ;[ids[index], ids[target]] = [ids[target]!, ids[index]!]
    const moved = episodes[index]!
    await guarded(async () => {
      replace(await reorderAdminEpisodes(season.id, ids))
      onAnnounce(
        `Moved ${moved.name} ${delta < 0 ? 'up' : 'down'} to position ${target + 1} of ${episodes.length}.`,
      )
    })
  }

  return (
    <article
      aria-label={label}
      className="flex flex-col gap-3 rounded-lg border border-surface-3 bg-surface-1 p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">{label}</h3>
        {confirmSeason ? (
          <div
            role="group"
            aria-label={`Confirm deleting ${label}`}
            className="flex flex-wrap items-center gap-2"
          >
            <span className="text-sm">
              Delete this season and all its episodes? This cannot be undone.
            </span>
            <Button
              size="sm"
              variant="secondary"
              disabled={busy}
              onClick={() =>
                void guarded(async () => {
                  await deleteAdminSeason(season.id)
                  await onChanged()
                })
              }
            >
              Yes, delete
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setConfirmSeason(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              aria-label={`Edit ${label}`}
              onClick={() => setEditing(true)}
            >
              Edit season
            </Button>
            <Button
              size="sm"
              variant="ghost"
              aria-label={`Delete ${label}`}
              onClick={() => setConfirmSeason(true)}
            >
              Delete season
            </Button>
          </div>
        )}
      </div>

      {editing ? (
        <SeasonForm
          initial={seasonToForm(season)}
          submitLabel="Save season"
          onCancel={() => setEditing(false)}
          onSubmit={async (v) => {
            await patchAdminSeason(season.id, seasonToBody(v))
            await onChanged()
            setEditing(false)
          }}
        />
      ) : null}

      {episodes.length === 0 && !addingEpisode ? (
        <p className="text-sm text-text-muted">No episodes yet.</p>
      ) : (
        <ol className="flex flex-col divide-y divide-surface-3 rounded-md border border-surface-3">
          {episodes.map((e, i) => (
            <li key={e.id} className="flex flex-col gap-2 p-3">
              {editingEpisode === e.id ? (
                <EpisodeForm
                  initial={episodeToForm(e)}
                  submitLabel="Save episode"
                  onCancel={() => setEditingEpisode(null)}
                  onSubmit={async (v) => {
                    await patchAdminEpisode(e.id, episodeToBody(v))
                    await onChanged()
                    setEditingEpisode(null)
                  }}
                />
              ) : (
                <div className="flex flex-wrap items-center gap-3">
                  <span aria-hidden="true" className="w-8 text-lg font-semibold text-text-muted">
                    {e.number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">
                      <span className="sr-only">{`Episode ${e.number}: `}</span>
                      {e.name}
                    </p>
                    <p className="text-sm text-text-muted">
                      {[
                        e.status === 'published' ? 'Published' : 'Draft',
                        formatRuntime(e.runtime_seconds),
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                  </div>
                  {confirmEpisode === e.id ? (
                    <div
                      role="group"
                      aria-label={`Confirm deleting ${e.name}`}
                      className="flex flex-wrap items-center gap-2"
                    >
                      <span className="text-sm">Delete this episode?</span>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() =>
                          void guarded(async () => {
                            await deleteAdminEpisode(e.id)
                            setConfirmEpisode(null)
                            await onChanged()
                          })
                        }
                      >
                        Yes, delete
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setConfirmEpisode(null)}>
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        className={moveClass}
                        aria-disabled={i === 0 || busy}
                        aria-label={`Move ${e.name} up`}
                        onClick={() => void move(i, -1)}
                      >
                        Up
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className={moveClass}
                        aria-disabled={i === episodes.length - 1 || busy}
                        aria-label={`Move ${e.name} down`}
                        onClick={() => void move(i, 1)}
                      >
                        Down
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        aria-label={`${e.status === 'published' ? 'Unpublish' : 'Publish'} ${e.name}`}
                        onClick={() =>
                          void guarded(async () => {
                            await patchAdminEpisode(e.id, {
                              status: e.status === 'published' ? 'draft' : 'published',
                            })
                            await onChanged()
                          })
                        }
                      >
                        {e.status === 'published' ? 'Unpublish' : 'Publish'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        aria-label={`Edit ${e.name}`}
                        onClick={() => setEditingEpisode(e.id)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={`Delete ${e.name}`}
                        onClick={() => setConfirmEpisode(e.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </li>
          ))}
        </ol>
      )}

      {addingEpisode ? (
        <EpisodeForm
          initial={episodeToForm(
            undefined,
            nextNumber(
              episodes.map((e) => e.number),
              1,
            ),
          )}
          submitLabel="Create episode"
          onCancel={() => setAddingEpisode(false)}
          onSubmit={async (v) => {
            await createAdminEpisode(season.id, episodeToBody(v))
            await onChanged()
            setAddingEpisode(false)
          }}
        />
      ) : (
        <div>
          <Button size="sm" variant="secondary" onClick={() => setAddingEpisode(true)}>
            {`Add episode to ${label}`}
          </Button>
        </div>
      )}
    </article>
  )
}
