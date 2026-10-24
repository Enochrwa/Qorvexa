import { api } from '@/lib/api/client'
import { unwrap } from '@/lib/api/errors'
import type { components } from '@/types/api'

export type AdminTitle = components['schemas']['AdminTitle']
export type AdminTitleItem = components['schemas']['AdminTitleItem']
export type TitleCreate = components['schemas']['TitleCreate']
export type TitlePatch = components['schemas']['TitlePatch']
export type PublishIn = components['schemas']['PublishIn']

export const PAGE = 25
export const adminKey = ['admin', 'titles'] as const

export type ListQuery = { status: string | null; q: string | null; offset: number }

export const listAdminTitles = (f: ListQuery) =>
  unwrap(
    api.GET('/api/v1/admin/titles', {
      params: {
        query: {
          status: f.status as 'draft' | 'scheduled' | 'published' | 'archived' | null,
          q: f.q,
          limit: PAGE,
          offset: f.offset,
        },
      },
    }),
  )

export const getAdminTitle = (id: string) =>
  unwrap(api.GET('/api/v1/admin/titles/{title_id}', { params: { path: { title_id: id } } }))

export const createAdminTitle = (body: TitleCreate) =>
  unwrap(api.POST('/api/v1/admin/titles', { body }))

export const patchAdminTitle = (id: string, body: TitlePatch) =>
  unwrap(api.PATCH('/api/v1/admin/titles/{title_id}', { params: { path: { title_id: id } }, body }))

export const deleteAdminTitle = (id: string) =>
  unwrap(api.DELETE('/api/v1/admin/titles/{title_id}', { params: { path: { title_id: id } } }))

export const publishAdminTitle = (id: string, body: PublishIn) =>
  unwrap(
    api.POST('/api/v1/admin/titles/{title_id}/publish', {
      params: { path: { title_id: id } },
      body,
    }),
  )

export const unpublishAdminTitle = (id: string) =>
  unwrap(
    api.POST('/api/v1/admin/titles/{title_id}/unpublish', { params: { path: { title_id: id } } }),
  )

// ---- seasons and episodes ------------------------------------------------------------------

export type AdminSeason = components['schemas']['AdminSeason']
export type AdminEpisode = components['schemas']['AdminEpisode']
export type SeasonCreate = components['schemas']['SeasonCreate']
export type SeasonPatch = components['schemas']['SeasonPatch']
export type EpisodeCreate = components['schemas']['EpisodeCreate']
export type EpisodePatch = components['schemas']['EpisodePatch']

export const seasonsKey = (titleId: string) => [...adminKey, titleId, 'seasons'] as const

export const listAdminSeasons = (titleId: string) =>
  unwrap(
    api.GET('/api/v1/admin/titles/{title_id}/seasons', { params: { path: { title_id: titleId } } }),
  )

export const createAdminSeason = (titleId: string, body: SeasonCreate) =>
  unwrap(
    api.POST('/api/v1/admin/titles/{title_id}/seasons', {
      params: { path: { title_id: titleId } },
      body,
    }),
  )

export const patchAdminSeason = (id: string, body: SeasonPatch) =>
  unwrap(
    api.PATCH('/api/v1/admin/seasons/{season_id}', { params: { path: { season_id: id } }, body }),
  )

export const deleteAdminSeason = (id: string) =>
  unwrap(api.DELETE('/api/v1/admin/seasons/{season_id}', { params: { path: { season_id: id } } }))

export const createAdminEpisode = (seasonId: string, body: EpisodeCreate) =>
  unwrap(
    api.POST('/api/v1/admin/seasons/{season_id}/episodes', {
      params: { path: { season_id: seasonId } },
      body,
    }),
  )

export const patchAdminEpisode = (id: string, body: EpisodePatch) =>
  unwrap(
    api.PATCH('/api/v1/admin/episodes/{episode_id}', {
      params: { path: { episode_id: id } },
      body,
    }),
  )

export const deleteAdminEpisode = (id: string) =>
  unwrap(
    api.DELETE('/api/v1/admin/episodes/{episode_id}', { params: { path: { episode_id: id } } }),
  )

export const reorderAdminEpisodes = (seasonId: string, episodeIds: string[]) =>
  unwrap(
    api.POST('/api/v1/admin/seasons/{season_id}/episodes/reorder', {
      params: { path: { season_id: seasonId } },
      body: { episode_ids: episodeIds },
    }),
  )
