import { api } from '@/lib/api/client'
import { ApiError, unwrap } from '@/lib/api/errors'
import { useProfile } from '@/features/profiles/store'
import { useSession } from '@/lib/api/session'

export const SORTS = ['added', 'name', 'year'] as const
export type Sort = (typeof SORTS)[number]
export type TitleType = 'movie' | 'series'

export type Filters = { type: TitleType | null; genre: string | null; sort: Sort }

export const PAGE_SIZE = 24

/**
 * The server answers 404 "Profile not found" when the selected profile no longer exists
 * (for example deleted on another device). Forget it and retry once without it, so the
 * user sees the catalog instead of an error.
 */
export async function withProfileRecovery<T>(call: () => Promise<T>): Promise<T> {
  try {
    return await call()
  } catch (err) {
    const stale =
      err instanceof ApiError &&
      err.status === 404 &&
      /profile not found/i.test(err.detail) &&
      useProfile.getState().selectedId !== null
    if (!stale) throw err
    const userId = useSession.getState().user?.id
    if (userId) useProfile.getState().forget(userId)
    else useProfile.getState().reset()
    return call()
  }
}

export const listTitles = (f: Filters, cursor: string | null) =>
  withProfileRecovery(() =>
    unwrap(
      api.GET('/api/v1/titles', {
        params: {
          query: {
            type: f.type,
            genre: f.genre,
            sort: f.sort,
            limit: PAGE_SIZE,
            cursor,
          },
        },
      }),
    ),
  )

export const getTitle = (slug: string) =>
  withProfileRecovery(() =>
    unwrap(api.GET('/api/v1/titles/{slug}', { params: { path: { slug } } })),
  )

export const listSeasons = (slug: string) =>
  withProfileRecovery(() =>
    unwrap(api.GET('/api/v1/titles/{slug}/seasons', { params: { path: { slug } } })),
  )

export const listGenres = () => unwrap(api.GET('/api/v1/genres'))
