import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { FormAlert } from '@/features/auth/AuthLayout'
import { applyFieldErrors } from '@/features/auth/field-errors'
import { ApiError } from '@/lib/api/errors'
import { adminMessage } from './messages'
import { seasonSchema, type SeasonFormValues } from './season-schemas'

export function SeasonForm(props: {
  initial: SeasonFormValues
  submitLabel: string
  onSubmit: (v: SeasonFormValues) => Promise<void>
  onCancel: () => void
}) {
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SeasonFormValues>({
    resolver: zodResolver(seasonSchema),
    defaultValues: props.initial,
  })

  const submit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await props.onSubmit(values)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError('number', { message: 'That season number is already used.' })
        return
      }
      if (applyFieldErrors(err, setError, ['number', 'name', 'synopsis'])) return
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
          label="Season number"
          inputMode="numeric"
          error={errors.number?.message}
          {...register('number')}
        />
        <Input label="Season name (optional)" error={errors.name?.message} {...register('name')} />
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="season-synopsis" className="text-sm text-text-muted">
          Season synopsis (optional)
        </label>
        <textarea
          id="season-synopsis"
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
