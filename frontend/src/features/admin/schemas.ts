import { z } from 'zod'
import { LANGUAGES, MATURITY } from '@/features/profiles/options'

const url = z
  .string()
  .trim()
  .max(2048, 'Use at most 2048 characters')
  .refine(
    (v) => v === '' || (v.startsWith('https://') && !/\s/.test(v)),
    'Use a full https:// address',
  )

export const ROLES = ['actor', 'director', 'writer'] as const

export const titleSchema = z.object({
  name: z.string().trim().min(1, 'Enter a name').max(200, 'Use at most 200 characters'),
  type: z.enum(['movie', 'series']),
  slug: z
    .string()
    .trim()
    .max(120)
    .refine(
      (v) => v === '' || /^[a-z0-9]+(-[a-z0-9]+)*$/.test(v),
      'Use lowercase letters, numbers and hyphens',
    ),
  original_name: z.string().trim().max(200, 'Use at most 200 characters'),
  synopsis: z.string().max(5000, 'Use at most 5000 characters'),
  release_year: z
    .string()
    .trim()
    .refine(
      (v) => v === '' || (/^\d{4}$/.test(v) && +v >= 1888 && +v <= 2100),
      'Enter a year between 1888 and 2100',
    ),
  maturity_rating: z.enum(MATURITY.map((m) => m.value) as [string, ...string[]]),
  language: z.string().refine((v) => v === '' || LANGUAGES.some((l) => l.code === v)),
  country: z
    .string()
    .trim()
    .refine((v) => v === '' || /^[A-Z]{2}$/.test(v), 'Use a 2-letter code such as RW'),
  poster_url: url,
  backdrop_url: url,
  downloads_enabled: z.boolean(),
  genres: z.array(z.string()),
  cast: z
    .array(
      z.object({
        name: z.string().trim().min(1, 'Enter a name').max(120, 'Use at most 120 characters'),
        role: z.enum(ROLES),
      }),
    )
    .max(50, 'At most 50 people')
    .refine(
      (rows) => new Set(rows.map((r) => `${r.name.toLowerCase()}|${r.role}`)).size === rows.length,
      'Each person can appear once per role',
    ),
})

export type TitleFormValues = z.infer<typeof titleSchema>
