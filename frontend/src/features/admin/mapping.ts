import type { AdminTitle, TitleCreate, TitlePatch } from './api'
import type { TitleFormValues } from './schemas'

const orNull = (v: string) => (v.trim() === '' ? null : v.trim())

export function emptyForm(): TitleFormValues {
  return {
    name: '',
    type: 'movie',
    slug: '',
    original_name: '',
    synopsis: '',
    release_year: '',
    maturity_rating: '18+',
    language: '',
    country: '',
    poster_url: '',
    backdrop_url: '',
    downloads_enabled: false,
    genres: [],
    cast: [],
  }
}

export function formFromTitle(t: AdminTitle): TitleFormValues {
  return {
    name: t.name,
    type: t.type as TitleFormValues['type'],
    slug: t.slug,
    original_name: t.original_name ?? '',
    synopsis: t.synopsis ?? '',
    release_year: t.release_year == null ? '' : String(t.release_year),
    maturity_rating: t.maturity_rating,
    language: t.language ?? '',
    country: t.country ?? '',
    poster_url: t.poster_url ?? '',
    backdrop_url: t.backdrop_url ?? '',
    downloads_enabled: t.downloads_enabled,
    genres: t.genres,
    cast: t.cast.map((c) => ({
      name: c.name,
      role: c.role as TitleFormValues['cast'][number]['role'],
    })),
  }
}

/** Blank optional fields become null (cleared) rather than empty strings. */
function shared(v: TitleFormValues) {
  return {
    name: v.name.trim(),
    original_name: orNull(v.original_name),
    synopsis: orNull(v.synopsis),
    release_year: v.release_year.trim() === '' ? null : Number(v.release_year),
    maturity_rating: v.maturity_rating as TitleCreate['maturity_rating'],
    language: orNull(v.language),
    country: orNull(v.country),
    poster_url: orNull(v.poster_url),
    backdrop_url: orNull(v.backdrop_url),
    downloads_enabled: v.downloads_enabled,
    genres: v.genres,
    cast: v.cast.map((c, i) => ({ name: c.name.trim(), role: c.role, billing_order: i })),
  }
}

export const toCreate = (v: TitleFormValues): TitleCreate => ({
  ...shared(v),
  type: v.type,
  slug: orNull(v.slug),
})

/** `slug` and `type` cannot change after creation, so they are never sent. */
export const toPatch = (v: TitleFormValues): TitlePatch => shared(v)

/** `datetime-local` has no time zone; the API requires one, so convert from the browser's. */
export function localToIso(value: string): string | null {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d.toISOString()
}
