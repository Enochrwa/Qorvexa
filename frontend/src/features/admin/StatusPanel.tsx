import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Button } from '@/components/Button'
import { FormAlert, Notice } from '@/features/auth/AuthLayout'
import {
  adminKey,
  deleteAdminTitle,
  publishAdminTitle,
  unpublishAdminTitle,
  type AdminTitle,
} from './api'
import { localToIso } from './mapping'
import { adminMessage } from './messages'
import { StateBadge } from './StateBadge'

const field = 'h-11 rounded-md border border-surface-3 bg-surface-1 px-3 text-text'

export function StatusPanel({
  title,
  onChanged,
  onDeleted,
}: {
  title: AdminTitle
  onChanged: (t: AdminTitle) => void
  onDeleted: () => void
}) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [publishAt, setPublishAt] = useState('')
  const [until, setUntil] = useState('')
  const [confirming, setConfirming] = useState(false)
  const published = title.status === 'published'
  const invalidate = () => queryClient.invalidateQueries({ queryKey: adminKey })

  const run =
    <T,>(fn: () => Promise<T>, then: (r: T) => void) =>
    async () => {
      setError(null)
      try {
        then(await fn())
        await invalidate()
      } catch (err) {
        setConfirming(false)
        setError(adminMessage(err))
      }
    }

  const publish = useMutation({
    mutationFn: () =>
      publishAdminTitle(title.id, {
        publish_at: localToIso(publishAt),
        available_until: localToIso(until),
      }),
  })
  const unpublish = useMutation({ mutationFn: () => unpublishAdminTitle(title.id) })
  const remove = useMutation({ mutationFn: () => deleteAdminTitle(title.id) })
  const busy = publish.isPending || unpublish.isPending || remove.isPending

  return (
    <section
      aria-labelledby="status-heading"
      className="flex flex-col gap-4 rounded-lg border border-surface-3 bg-surface-1 p-4"
    >
      <div className="flex items-center gap-3">
        <h2 id="status-heading" className="text-lg font-semibold">
          Publishing
        </h2>
        <StateBadge state={title.state} />
      </div>
      <FormAlert message={error} />
      {title.state === 'scheduled' && title.publish_at ? (
        <Notice>{`Hidden from viewers until ${new Date(title.publish_at).toLocaleString()}.`}</Notice>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Publish at (optional, your local time)
          <input
            type="datetime-local"
            className={field}
            value={publishAt}
            onChange={(e) => setPublishAt(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Available until (optional)
          <input
            type="datetime-local"
            className={field}
            value={until}
            onChange={(e) => setUntil(e.target.value)}
          />
        </label>
      </div>

      <div className="flex flex-wrap gap-3">
        <Button disabled={busy} onClick={run(() => publish.mutateAsync(), onChanged)}>
          {published ? 'Update schedule' : 'Publish'}
        </Button>
        {published ? (
          <Button
            variant="secondary"
            disabled={busy}
            onClick={run(() => unpublish.mutateAsync(), onChanged)}
          >
            Unpublish
          </Button>
        ) : null}
      </div>

      <div className="border-t border-surface-3 pt-4">
        {confirming ? (
          <div
            role="group"
            aria-label="Confirm deleting this title"
            className="flex flex-wrap items-center gap-3"
          >
            <span className="text-sm">
              Delete “{title.name}” and its seasons and episodes? This cannot be undone.
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={busy}
              onClick={run(() => remove.mutateAsync(), onDeleted)}
            >
              Yes, delete
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-start gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={published || busy}
              onClick={() => setConfirming(true)}
            >
              Delete title
            </Button>
            {published ? (
              <p className="text-xs text-text-muted">Unpublish a title before deleting it.</p>
            ) : null}
          </div>
        )}
      </div>
    </section>
  )
}
