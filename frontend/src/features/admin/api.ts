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
