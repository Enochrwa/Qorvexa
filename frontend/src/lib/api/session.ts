import { create } from 'zustand'
import type { components } from '@/types/api'

export type Me = components['schemas']['MeOut']
export type SessionStatus = 'loading' | 'anonymous' | 'authenticated'

type SessionState = {
  status: SessionStatus
  /** Held in memory only. Never written to localStorage, sessionStorage or cookies. */
  accessToken: string | null
  user: Me | null
  setToken: (token: string) => void
  setUser: (user: Me) => void
  clear: () => void
}

export const useSession = create<SessionState>((set) => ({
  status: 'loading',
  accessToken: null,
  user: null,
  setToken: (accessToken) => set({ accessToken }),
  setUser: (user) => set({ user, status: 'authenticated' }),
  clear: () => set({ accessToken: null, user: null, status: 'anonymous' }),
}))
