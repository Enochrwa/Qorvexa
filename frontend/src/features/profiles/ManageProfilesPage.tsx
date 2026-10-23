import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import { FormAlert } from '@/features/auth/AuthLayout'
import { friendlyMessage } from '@/lib/api/errors'
import { useSession } from '@/lib/api/session'
import {
  createProfile,
  deleteProfile,
  MAX_PROFILES,
  profilesKey,
  updateProfile,
  type Profile,
} from './api'
import { Avatar } from './Avatar'
import { useProfiles } from './hooks'
import { ProfileForm, toInput } from './ProfileForm'
import { useProfile } from './store'

type Mode = { kind: 'list' } | { kind: 'create' } | { kind: 'edit'; profile: Profile }

export function ManageProfilesPage() {
  const queryClient = useQueryClient()
  const userId = useSession((s) => s.user?.id)
  const { data: profiles, isPending, isError } = useProfiles()
  const [mode, setMode] = useState<Mode>({ kind: 'list' })
  const [confirming, setConfirming] = useState<string | null>(null)
  const [listError, setListError] = useState<string | null>(null)

  const refresh = () => queryClient.invalidateQueries({ queryKey: profilesKey })

  const remove = useMutation({
    mutationFn: deleteProfile,
    onSuccess: async (_d, id) => {
      if (userId && useProfile.getState().selectedId === id) useProfile.getState().forget(userId)
      setConfirming(null)
      setListError(null)
      await refresh()
    },
    onError: (err) => {
      setConfirming(null)
      setListError(
        /only profile/i.test((err as Error).message)
          ? 'You cannot delete your only profile.'
          : friendlyMessage(err),
      )
    },
  })

  if (isPending) {
    return (
      <div role="status" aria-label="Loading profiles" className="py-8">
        <Skeleton className="h-8 w-64" />
      </div>
    )
  }
  if (isError)
    return (
      <p role="alert" className="py-8 text-danger">
        We could not load your profiles.
      </p>
    )

  if (mode.kind !== 'list') {
    const editing = mode.kind === 'edit' ? mode.profile : undefined
    return (
      <section className="mx-auto flex max-w-xl flex-col gap-6 py-8">
        <h1 className="text-2xl font-semibold">{editing ? 'Edit profile' : 'Add profile'}</h1>
        <ProfileForm
          profile={editing}
          submitLabel={editing ? 'Save changes' : 'Create profile'}
          onCancel={() => setMode({ kind: 'list' })}
          onSubmit={async (values) => {
            if (editing) await updateProfile(editing.id, toInput(values))
            else await createProfile(toInput(values))
            await refresh()
            setMode({ kind: 'list' })
          }}
        />
      </section>
    )
  }

  const atLimit = profiles.length >= MAX_PROFILES
  const onlyOne = profiles.length <= 1

  return (
    <section className="mx-auto flex max-w-2xl flex-col gap-6 py-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Manage profiles</h1>
        <Link to="/profiles" className="text-accent underline">
          Back to profiles
        </Link>
      </div>
      <FormAlert message={listError} />
      <ul className="flex flex-col gap-3">
        {profiles.map((p) => (
          <li
            key={p.id}
            className="flex flex-wrap items-center gap-4 rounded-lg border border-surface-3 bg-surface-1 p-3"
          >
            <Avatar avatar={p.avatar} name={p.name} className="h-12 w-12 text-xl" />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{p.name}</p>
              <p className="text-sm text-text-muted">
                {p.maturity_limit === 'all' ? 'All ages' : p.maturity_limit}
              </p>
            </div>
            {confirming === p.id ? (
              <div
                role="group"
                aria-label={`Confirm deleting ${p.name}`}
                className="flex items-center gap-2"
              >
                <span className="text-sm">Delete {p.name}? This cannot be undone.</span>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => remove.mutate(p.id)}
                  disabled={remove.isPending}
                >
                  Yes, delete
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirming(null)}>
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  aria-label={`Edit ${p.name}`}
                  onClick={() => setMode({ kind: 'edit', profile: p })}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Delete ${p.name}`}
                  disabled={onlyOne}
                  title={onlyOne ? 'You cannot delete your only profile' : undefined}
                  onClick={() => setConfirming(p.id)}
                >
                  Delete
                </Button>
              </div>
            )}
          </li>
        ))}
      </ul>
      <div className="flex flex-col items-start gap-2">
        <Button onClick={() => setMode({ kind: 'create' })} disabled={atLimit}>
          Add profile
        </Button>
        <p className="text-sm text-text-muted">
          {atLimit
            ? `You have reached the maximum of ${MAX_PROFILES} profiles.`
            : `${profiles.length} of ${MAX_PROFILES} profiles used.`}
        </p>
      </div>
    </section>
  )
}
