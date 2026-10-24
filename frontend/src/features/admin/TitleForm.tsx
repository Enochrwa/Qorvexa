import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useFieldArray, useForm, useWatch } from 'react-hook-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { FormAlert } from '@/features/auth/AuthLayout'
import { applyFieldErrors } from '@/features/auth/field-errors'
import { useGenres } from '@/features/catalog/hooks'
import { LANGUAGES, MATURITY } from '@/features/profiles/options'
import { ApiError } from '@/lib/api/errors'
import { adminMessage } from './messages'
import { ROLES, titleSchema, type TitleFormValues } from './schemas'

const field = 'h-11 rounded-md border border-surface-3 bg-surface-1 px-3 text-text'
const FIELDS = [
  'name',
  'slug',
  'original_name',
  'synopsis',
  'release_year',
  'country',
  'poster_url',
  'backdrop_url',
]

export function TitleForm(props: {
  mode: 'create' | 'edit'
  initial: TitleFormValues
  onSubmit: (values: TitleFormValues) => Promise<void>
  onCancel: () => void
}) {
  const editing = props.mode === 'edit'
  const genres = useGenres()
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<TitleFormValues>({ resolver: zodResolver(titleSchema), defaultValues: props.initial })
  const cast = useFieldArray({ control, name: 'cast' })
  const synopsisLength = (useWatch({ control, name: 'synopsis' }) ?? '').length

  const submit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await props.onSubmit(values)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409 && /slug/i.test(err.detail)) {
        setError('slug', { message: 'That slug is already used by another title.' })
        return
      }
      if (applyFieldErrors(err, setError, FIELDS)) return
      setFormError(adminMessage(err))
    }
  })

  return (
    <form
      onSubmit={submit}
      noValidate
      aria-busy={isSubmitting}
      className="flex max-w-3xl flex-col gap-6"
    >
      <FormAlert message={formError} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Name" error={errors.name?.message} {...register('name')} />
        <Input
          label="Original name (optional)"
          error={errors.original_name?.message}
          {...register('original_name')}
        />
        <div className="flex flex-col gap-1 text-sm text-text-muted">
          <label htmlFor="title-type">Type</label>
          <select
            id="title-type"
            className={field}
            disabled={editing}
            aria-describedby={editing ? 'type-hint' : undefined}
            {...register('type')}
          >
            <option value="movie">Movie</option>
            <option value="series">Series</option>
          </select>
          {editing ? (
            <span id="type-hint" className="text-xs">
              The type cannot be changed after creation.
            </span>
          ) : null}
        </div>
        <div className="flex flex-col gap-1">
          <Input
            label={editing ? 'Slug (address)' : 'Slug (optional, made from the name)'}
            readOnly={editing}
            error={errors.slug?.message}
            {...register('slug')}
          />
          {editing ? (
            <span className="text-xs text-text-muted">
              The slug cannot be changed, so links keep working.
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="synopsis" className="text-sm text-text-muted">
          Synopsis
        </label>
        <textarea
          id="synopsis"
          rows={5}
          aria-invalid={errors.synopsis ? true : undefined}
          aria-describedby="synopsis-count"
          className="rounded-md border border-surface-3 bg-surface-1 p-3 text-text"
          {...register('synopsis')}
        />
        <p
          id="synopsis-count"
          className={errors.synopsis ? 'text-sm text-danger' : 'text-xs text-text-muted'}
        >
          {errors.synopsis?.message ?? `${synopsisLength} of 5000 characters`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <Input
          label="Release year"
          inputMode="numeric"
          error={errors.release_year?.message}
          {...register('release_year')}
        />
        <div className="flex flex-col gap-1 text-sm text-text-muted sm:col-span-2">
          <label htmlFor="title-rating">Maturity rating</label>
          <select
            id="title-rating"
            className={field}
            aria-describedby="rating-hint"
            {...register('maturity_rating')}
          >
            {MATURITY.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
          <span id="rating-hint" className="text-xs">
            New titles start at 18+ (most restricted). Lower it on purpose.
          </span>
        </div>
        <label className="flex flex-col gap-1 text-sm text-text-muted">
          Language
          <select className={field} {...register('language')}>
            <option value="">Not set</option>
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
        <Input
          label="Country (2 letters)"
          maxLength={2}
          error={errors.country?.message}
          {...register('country')}
        />
      </div>

      <div className="grid gap-4">
        <Input
          label="Poster image address (https)"
          error={errors.poster_url?.message}
          {...register('poster_url')}
        />
        <Input
          label="Backdrop image address (https)"
          error={errors.backdrop_url?.message}
          {...register('backdrop_url')}
        />
      </div>

      <label className="flex items-center gap-2">
        <input type="checkbox" className="h-5 w-5" {...register('downloads_enabled')} />
        Allow downloads for this title
      </label>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm text-text-muted">Genres</legend>
        {genres.isPending ? (
          <p role="status" className="text-sm text-text-muted">
            Loading genres…
          </p>
        ) : genres.isError ? (
          <p role="alert" className="text-sm text-danger">
            Genres could not be loaded.
          </p>
        ) : (
          <div className="flex flex-wrap gap-x-5 gap-y-2">
            {genres.data.map((g) => (
              <label key={g.slug} className="flex items-center gap-2">
                <input type="checkbox" value={g.slug} className="h-5 w-5" {...register('genres')} />
                {g.name}
              </label>
            ))}
          </div>
        )}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="text-sm text-text-muted">
          Cast and crew (billing order follows the list)
        </legend>
        {cast.fields.map((row, i) => (
          <div key={row.id} className="flex flex-wrap items-end gap-3">
            <div className="min-w-48 flex-1">
              <Input
                label={`Person ${i + 1} name`}
                error={errors.cast?.[i]?.name?.message}
                {...register(`cast.${i}.name`)}
              />
            </div>
            <label className="flex flex-col gap-1 text-sm text-text-muted">
              {`Person ${i + 1} role`}
              <select className={field} {...register(`cast.${i}.role`)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r[0]?.toUpperCase() + r.slice(1)}
                  </option>
                ))}
              </select>
            </label>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => cast.remove(i)}
              aria-label={`Remove person ${i + 1}`}
            >
              Remove
            </Button>
          </div>
        ))}
        {errors.cast?.root?.message ||
        (typeof errors.cast?.message === 'string' && errors.cast.message) ? (
          <p role="alert" className="text-sm text-danger">
            {errors.cast?.root?.message ?? String(errors.cast?.message)}
          </p>
        ) : null}
        <div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={cast.fields.length >= 50}
            onClick={() => cast.append({ name: '', role: 'actor' })}
          >
            Add person
          </Button>
        </div>
      </fieldset>

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : editing ? 'Save changes' : 'Create title'}
        </Button>
        <Button type="button" variant="secondary" onClick={props.onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
