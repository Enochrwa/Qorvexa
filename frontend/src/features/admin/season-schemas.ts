import { z } from 'zod'

const optionalSeconds = z
  .string()
  .trim()
  .refine(
    (v) => v === '' || (/^\d{1,5}$/.test(v) && +v <= 43200),
    'Use whole seconds from 0 to 43200',
  )

export const seasonSchema = z.object({
  number: z
    .string()
    .trim()
    .regex(/^\d{1,3}$/, 'Enter a number from 0 to 100')
    .refine((v) => +v <= 100, 'Enter a number from 0 to 100'),
  name: z.string().trim().max(200, 'Use at most 200 characters'),
  synopsis: z.string().max(5000, 'Use at most 5000 characters'),
})
export type SeasonFormValues = z.infer<typeof seasonSchema>

export const episodeSchema = z
  .object({
    number: z
      .string()
      .trim()
      .regex(/^\d{1,3}$/, 'Enter a number from 1 to 500')
      .refine((v) => +v >= 1 && +v <= 500, 'Enter a number from 1 to 500'),
    name: z.string().trim().min(1, 'Enter a name').max(200, 'Use at most 200 characters'),
    synopsis: z.string().max(5000, 'Use at most 5000 characters'),
    runtime_min: z
      .string()
      .trim()
      .refine(
        (v) => v === '' || (/^\d{1,3}$/.test(v) && +v <= 720),
        'Use whole minutes from 0 to 720',
      ),
    runtime_sec: z
      .string()
      .trim()
      .refine((v) => v === '' || (/^\d{1,2}$/.test(v) && +v <= 59), 'Use 0 to 59'),
    air_date: z
      .string()
      .refine((v) => v === '' || /^\d{4}-\d{2}-\d{2}$/.test(v), 'Use a valid date'),
    intro_start: optionalSeconds,
    intro_end: optionalSeconds,
    recap_end: optionalSeconds,
    published: z.boolean(),
  })
  .superRefine((v, ctx) => {
    const runtime = runtimeSeconds(v.runtime_min, v.runtime_sec)
    const num = (s: string) => (s === '' ? null : Number(s))
    const [s, e, r] = [num(v.intro_start), num(v.intro_end), num(v.recap_end)]
    if (s !== null && e !== null && e < s) {
      ctx.addIssue({
        code: 'custom',
        path: ['intro_end'],
        message: 'The intro cannot end before it starts',
      })
    }
    if (runtime !== null) {
      for (const [path, val] of [
        ['intro_start', s],
        ['intro_end', e],
        ['recap_end', r],
      ] as const) {
        if (val !== null && val > runtime) {
          ctx.addIssue({
            code: 'custom',
            path: [path],
            message: 'Cannot be later than the runtime',
          })
        }
      }
    }
  })
export type EpisodeFormValues = z.infer<typeof episodeSchema>

/** Minutes and seconds fields to total seconds; null when both are blank or zero. */
export function runtimeSeconds(min: string, sec: string): number | null {
  if (min.trim() === '' && sec.trim() === '') return null
  const total = Number(min || 0) * 60 + Number(sec || 0)
  return total > 0 ? total : null
}

export function splitRuntime(seconds: number | null): { min: string; sec: string } {
  if (!seconds) return { min: '', sec: '' }
  return { min: String(Math.floor(seconds / 60)), sec: String(seconds % 60) }
}
