import { create } from 'zustand'

/**
 * The selected profile id is a convenience, not a secret: it is useless without a signed-in
 * session of the owning account, and the server re-checks ownership on every request.
 * It is remembered per account in localStorage so a reload keeps the same profile.
 */
const key = (userId: string) => `qorvexa.profile.${userId}`

function read(userId: string): string | null {
  try {
    return localStorage.getItem(key(userId))
  } catch {
    return null // storage blocked (private mode, policy): fall back to choosing again
  }
}

function write(userId: string, profileId: string | null) {
  try {
    if (profileId) localStorage.setItem(key(userId), profileId)
    else localStorage.removeItem(key(userId))
  } catch {
    /* ignore */
  }
}

type ProfileState = {
  selectedId: string | null
  /** Load the remembered choice for this account (called when a session starts). */
  hydrate: (userId: string) => void
  select: (userId: string, profileId: string) => void
  /** Forget the choice for this account (profile deleted or no longer valid). */
  forget: (userId: string) => void
  /** Drop the in-memory choice on sign out. The remembered choice stays for the next sign in. */
  reset: () => void
}

export const useProfile = create<ProfileState>((set) => ({
  selectedId: null,
  hydrate: (userId) => set({ selectedId: read(userId) }),
  select: (userId, profileId) => {
    write(userId, profileId)
    set({ selectedId: profileId })
  },
  forget: (userId) => {
    write(userId, null)
    set({ selectedId: null })
  },
  reset: () => set({ selectedId: null }),
}))
