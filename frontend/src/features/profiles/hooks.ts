import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useSession } from '@/lib/api/session'
import { listProfiles, profilesKey, type Profile } from './api'
import { useProfile } from './store'

export function useProfiles() {
  const signedIn = useSession((s) => s.status === 'authenticated')
  return useQuery({ queryKey: profilesKey, queryFn: listProfiles, enabled: signedIn })
}

/**
 * The profile currently in use, validated against the account's real profiles.
 * A remembered id that no longer exists (deleted elsewhere) is forgotten; a single
 * profile is selected automatically.
 */
export function useCurrentProfile(): {
  profile: Profile | null
  profiles: Profile[]
  loading: boolean
  error: boolean
} {
  const userId = useSession((s) => s.user?.id)
  const selectedId = useProfile((s) => s.selectedId)
  const query = useProfiles()
  const profiles = query.data ?? []
  const current = profiles.find((p) => p.id === selectedId) ?? null

  useEffect(() => {
    if (!userId || !query.data) return
    if (selectedId && !current) useProfile.getState().forget(userId)
    else if (!selectedId && query.data.length === 1 && query.data[0]) {
      useProfile.getState().select(userId, query.data[0].id)
    }
  }, [userId, query.data, selectedId, current])

  return { profile: current, profiles, loading: query.isPending, error: query.isError }
}
