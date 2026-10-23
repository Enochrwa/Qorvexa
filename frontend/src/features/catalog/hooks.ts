import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { useProfile } from '@/features/profiles/store'
import { getTitle, listGenres, listSeasons, listTitles, type Filters } from './api'

/** Catalog answers depend on the selected profile, so it is part of every cache key. */
const useAudience = () => useProfile((s) => s.selectedId ?? 'default')

export function useGenres() {
  return useQuery({ queryKey: ['genres'], queryFn: listGenres, staleTime: 5 * 60_000 })
}

export function useTitles(filters: Filters) {
  const audience = useAudience()
  return useInfiniteQuery({
    queryKey: ['titles', audience, filters],
    queryFn: ({ pageParam }) => listTitles(filters, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  })
}

export function useTitle(slug: string) {
  const audience = useAudience()
  return useQuery({
    queryKey: ['title', audience, slug],
    queryFn: () => getTitle(slug),
  })
}

export function useSeasons(slug: string, enabled: boolean) {
  const audience = useAudience()
  return useQuery({
    queryKey: ['seasons', audience, slug],
    queryFn: () => listSeasons(slug),
    enabled,
  })
}
