import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { FormAlert } from '@/features/auth/AuthLayout'
import { applyFieldErrors } from '@/features/auth/field-errors'
import { friendlyMessage, ApiError } from '@/lib/api/errors'
import type { Profile, ProfileInput } from './api'
import { Avatar, avatarColor } from './Avatar'
import { AVATARS, LANGUAGES, MATURITY, SUBTITLE_SIZES } from './options'
import { profileSchema, type ProfileFormValues } from './schemas'

const fieldClass = 'h-11 rounded-md border border-surface-3 bg-surface-1 px-3 text-text'

export function toInput(v: ProfileFormValues): ProfileInput {
  return {
    name: v.name,
    avatar: v.avatar,
    language: v.language,
    maturity_limit: v.maturity_limit as ProfileInput['maturity_limit'],
    autoplay_next: v.autoplay_next,
    data_saver: v.data_saver,
    subtitle_prefs: { enabled: v.subtitles_enabled, size: v.subtitles_size },
  }
}

function defaults(p?: Profile): ProfileFormValues {
  const subs = (p?.subtitle_prefs ?? {}) as { enabled?: boolean; size?: string }
  return {
    name: p?.name ?? '',
    avatar: p?.avatar ?? 'avatar-1',
    language: p?.language ?? 'en',
    maturity_limit: p?.maturity_limit ?? '13+',
    autoplay_next: p?.autoplay_next ?? true,
    data_saver: p?.data_saver ?? false,
    subtitles_enabled: subs.enabled ?? false,
    subtitles_size: (SUBTITLE_SIZES as readonly string[]).includes(subs.size ?? '')
      ? (subs.size as ProfileFormValues['subtitles_size'])
      : 'medium',
  }
}

function conflictMessage(err: unknown): string {
  if (err instanceof ApiError && err.status === 409) {
    if (/at most/i.test(err.detail)) return 'You have reached the maximum number of profiles.'
    return 'You already have a profile with that name.'
  }
  return friendlyMessage(err)
}

export function ProfileForm(props: {
  profile?: Profile
  submitLabel: string
  onSubmit: (values: ProfileFormValues) => Promise<void>
  onCancel: () => void
}) {
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: defaults(props.profile),
  })
  const name = useWatch({ control, name: 'name' })
  const avatar = useWatch({ control, name: 'avatar' })

  const submit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await props.onSubmit(values)
    } catch (err) {
      if (applyFieldErrors(err, setError, ['name', 'language'])) return
      setFormError(conflictMessage(err))
    }
  })

  return (
    <form onSubmit={submit} noValidate aria-busy={isSubmitting} className="flex flex-col gap-5">
      <FormAlert message={formError} />
      <div className="flex items-center gap-4">
        <Avatar avatar={avatar} name={name || '?'} />
        <div className="flex-1">
          <Input
            label="Name"
            autoComplete="off"
            maxLength={80}
            error={errors.name?.message}
            {...register('name')}
          />
        </div>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm text-text-muted">Avatar</legend>
        <div className="flex flex-wrap gap-2">
          {AVATARS.map((a, i) => (
            <label key={a} className="cursor-pointer">
              <input type="radio" value={a} className="peer sr-only" {...register('avatar')} />
              <span
                style={{ backgroundColor: avatarColor(a) }}
                className="flex h-10 w-10 items-center justify-center rounded-md text-sm font-semibold text-white ring-offset-2 ring-offset-surface-1 peer-checked:ring-2 peer-checked:ring-white peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-accent"
              >
                <span className="sr-only">{`Avatar ${i + 1}`}</span>
                <span aria-hidden="true">{i + 1}</span>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Language
          <select className={fieldClass} {...register('language')}>
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Maturity limit
          <select className={fieldClass} {...register('maturity_limit')}>
            {MATURITY.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm text-text-muted">Playback</legend>
        <label className="flex items-center gap-2">
          <input type="checkbox" className="h-5 w-5" {...register('autoplay_next')} />
          Play the next episode automatically
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" className="h-5 w-5" {...register('data_saver')} />
          Data saver (lower video quality)
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" className="h-5 w-5" {...register('subtitles_enabled')} />
          Show subtitles by default
        </label>
        <label className="flex flex-col gap-1 text-sm text-text-muted sm:max-w-xs">
          Subtitle size
          <select className={fieldClass} {...register('subtitles_size')}>
            {SUBTITLE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s[0]?.toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </fieldset>

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : props.submitLabel}
        </Button>
        <Button type="button" variant="secondary" onClick={props.onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
