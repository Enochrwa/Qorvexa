import { SORTS, type Filters, type Sort } from './api'

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/

/** Read filters from the URL. Anything unexpected is ignored: the URL is user input. */
export function parseFilters(params: URLSearchParams): Filters {
  const type = params.get('type')
  const genre = params.get('genre')
  const sort = params.get('sort')
  return {
    type: type === 'movie' || type === 'series' ? type : null,
    genre: genre && genre.length <= 60 && SLUG.test(genre) ? genre : null,
    sort: (SORTS as readonly string[]).includes(sort ?? '') ? (sort as Sort) : 'added',
  }
}

/** Write filters to the URL, leaving defaults out so the common URL stays short. */
export function toSearchParams(f: Filters): URLSearchParams {
  const p = new URLSearchParams()
  if (f.type) p.set('type', f.type)
  if (f.genre) p.set('genre', f.genre)
  if (f.sort !== 'added') p.set('sort', f.sort)
  return p
}

export function formatRuntime(seconds: number | null | undefined): string | null {
  if (!seconds || seconds < 1) return null
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h} h ${m} min` : `${h} h`
}

/** Only https images are rendered, whatever the API returns (defence in depth). */
export function safeImageUrl(url: string | null | undefined): string | null {
  return url && url.startsWith('https://') ? url : null
}

export function ratingLabel(rating: string): string {
  return rating === 'all' ? 'All ages' : rating
}
