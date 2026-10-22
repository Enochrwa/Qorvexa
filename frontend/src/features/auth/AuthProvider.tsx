import { useEffect, type ReactNode } from 'react'
import { restoreSession } from './api'

/** Restores the session from the refresh cookie once when the app loads. */
export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    void restoreSession()
  }, [])
  return children
}
