import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { FormAlert } from '@/features/auth/AuthLayout'
import { applyFieldErrors } from '@/features/auth/field-errors'
import { ApiError } from '@/lib/api/errors'
import { adminMessage } from './messages'
import { episodeSchema, type EpisodeFormValues } from './season-schemas'

export function EpisodeForm(props: {
  initial: EpisodeFormValues
  submitLabel: string
  onSubmit: (v: EpisodeFormValues) => Promise<void>
  onCancel: () => void
}) {
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<EpisodeFormValues>({
    resolver: zodResolver(episodeSchema),
    defaultValues: props.initial,
  })

  const submit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await props.onSubmit(values)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError('number', { message: 'That episode number is already used in this season.' })
        return
      }
      if (applyFieldErrors(err, setError, ['number', 'name', 'synopsis', 'air_date'])) return
      setFormError(adminMessage(err))
    }
  })

  return (
    <form
      onSubmit={submit}
      noValidate
      aria-busy={isSubmitting}
      className="flex flex-col gap-3 rounded-lg border border-surface-3 bg-surface-2 p-4"
    >
      <FormAlert message={formError} />
      <div className="grid gap-3 sm:grid-cols-[8rem_1fr]">
        <Input
          label="Episode number"
          inputMode="numeric"
          error={errors.number?.message}
          {...register('number')}
        />
        <Input label="Episode name" error={errors.name?.message} {...register('name')} />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="episode-synopsis" className="text-sm text-text-muted">
          Episode synopsis (optional)
        </label>
        <textarea
          id="episode-synopsis"
          rows={3}
          className="rounded-md border border-surface-3 bg-surface-1 p-3 text-text"
          {...register('synopsis')}
        />
        {errors.synopsis ? (
          <p role="alert" className="text-sm text-danger">
            {errors.synopsis.message}
          </p>
        ) : null}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Input
          label="Runtime minutes"
          inputMode="numeric"
          error={errors.runtime_min?.message}
          {...register('runtime_min')}
        />
        <Input
          label="Runtime seconds"
          inputMode="numeric"
          error={errors.runtime_sec?.message}
          {...register('runtime_sec')}
        />
        <Input
          label="Air date"
          type="date"
          error={errors.air_date?.message}
          {...register('air_date')}
        />
      </div>
      <details className="rounded-md border border-surface-3 p-3">
        <summary className="cursor-pointer text-sm">Skip markers (optional, in seconds)</summary>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <Input
            label="Intro starts at"
            inputMode="numeric"
            error={errors.intro_start?.message}
            {...register('intro_start')}
          />
          <Input
            label="Intro ends at"
            inputMode="numeric"
            error={errors.intro_end?.message}
            {...register('intro_end')}
          />
          <Input
            label="Recap ends at"
            inputMode="numeric"
            error={errors.recap_end?.message}
            {...register('recap_end')}
          />
        </div>
      </details>
      <label className="flex items-center gap-2">
        <input type="checkbox" className="h-5 w-5" {...register('published')} />
        Published (viewers can see this episode)
      </label>
      <div className="flex gap-3">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : props.submitLabel}
        </Button>
        <Button type="button" size="sm" variant="secondary" onClick={props.onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
