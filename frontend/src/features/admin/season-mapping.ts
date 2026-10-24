import type { AdminEpisode, AdminSeason, EpisodeCreate, SeasonCreate } from './api'
import type { EpisodeFormValues, SeasonFormValues } from './season-schemas'
import { runtimeSeconds, splitRuntime } from './season-schemas'

const orNull = (v: string) => (v.trim() === '' ? null : v.trim())
const secs = (v: string) => (v.trim() === '' ? null : Number(v))

export const seasonToBody = (v: SeasonFormValues): SeasonCreate => ({
  number: Number(v.number),
  name: orNull(v.name),
  synopsis: orNull(v.synopsis),
})

export const seasonToForm = (s?: AdminSeason, nextNumber = 1): SeasonFormValues => ({
  number: String(s?.number ?? nextNumber),
  name: s?.name ?? '',
  synopsis: s?.synopsis ?? '',
})

export const episodeToBody = (v: EpisodeFormValues): EpisodeCreate => ({
  number: Number(v.number),
  name: v.name.trim(),
  synopsis: orNull(v.synopsis),
  runtime_seconds: runtimeSeconds(v.runtime_min, v.runtime_sec),
  air_date: orNull(v.air_date),
  intro_start: secs(v.intro_start),
  intro_end: secs(v.intro_end),
  recap_end: secs(v.recap_end),
  status: v.published ? 'published' : 'draft',
})

export function episodeToForm(e?: AdminEpisode, nextNumber = 1): EpisodeFormValues {
  const { min, sec } = splitRuntime(e?.runtime_seconds ?? null)
  return {
    number: String(e?.number ?? nextNumber),
    name: e?.name ?? '',
    synopsis: e?.synopsis ?? '',
    runtime_min: min,
    runtime_sec: sec,
    air_date: e?.air_date ?? '',
    intro_start: e?.intro_start == null ? '' : String(e.intro_start),
    intro_end: e?.intro_end == null ? '' : String(e.intro_end),
    recap_end: e?.recap_end == null ? '' : String(e.recap_end),
    published: e?.status === 'published',
  }
}

export const nextNumber = (numbers: number[], first: number) =>
  numbers.length ? Math.max(...numbers) + 1 : first
