import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { resetRestoreForTests } from '@/features/auth/api'
import { useProfile } from '@/features/profiles/store'
import { useSession } from '@/lib/api/session'
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  resetRestoreForTests()
  useSession.setState({ status: 'loading', accessToken: null, user: null })
  useProfile.setState({ selectedId: null })
  localStorage.clear()
  sessionStorage.clear()
})
afterAll(() => server.close())
