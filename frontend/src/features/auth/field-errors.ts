import type { FieldPath, FieldValues, UseFormSetError } from 'react-hook-form'
import { ApiError } from '@/lib/api/errors'

/** Show server-side validation errors (422) next to the matching fields. Returns true if any matched. */
export function applyFieldErrors<T extends FieldValues>(
  err: unknown,
  setError: UseFormSetError<T>,
  fields: readonly string[],
): boolean {
  if (!(err instanceof ApiError) || err.status !== 422) return false
  let matched = false
  for (const e of err.fieldErrors) {
    const name = e.loc[e.loc.length - 1]
    if (name && fields.includes(name)) {
      setError(name as FieldPath<T>, { message: e.msg })
      matched = true
    }
  }
  return matched
}
