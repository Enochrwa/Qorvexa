import { api } from '@/lib/api/client'
import { unwrap } from '@/lib/api/errors'
import type { components } from '@/types/api'

export type Profile = components['schemas']['ProfileOut']
export type ProfileInput = components['schemas']['ProfileCreate']

export const MAX_PROFILES = 5

export const profilesKey = ['profiles'] as const

export const listProfiles = () => unwrap(api.GET('/api/v1/profiles'))

export const createProfile = (body: ProfileInput) => unwrap(api.POST('/api/v1/profiles', { body }))

export const updateProfile = (id: string, body: Partial<ProfileInput>) =>
  unwrap(api.PATCH('/api/v1/profiles/{profile_id}', { params: { path: { profile_id: id } }, body }))

export const deleteProfile = (id: string) =>
  unwrap(api.DELETE('/api/v1/profiles/{profile_id}', { params: { path: { profile_id: id } } }))
