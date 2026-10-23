import { useQueryClient } from '@tanstack/react-query'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { Button } from '@/components/Button'
import { logout } from '@/features/auth/api'
import { useCurrentProfile } from '@/features/profiles/hooks'
import { useSession } from '@/lib/api/session'

export function AppShell() {
  const status = useSession((s) => s.status)
  const user = useSession((s) => s.user)
  const { profile } = useCurrentProfile()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  async function onSignOut() {
    try {
      await logout()
    } catch {
      /* the local session is cleared regardless */
    }
    queryClient.clear() // drop any cached data that belonged to the signed-in user
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-surface-2 bg-surface-1">
        <nav aria-label="Primary" className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
          <Link to="/" className="text-xl font-bold tracking-tight text-accent">
            Qorvexa
          </Link>
          <div className="ml-auto flex items-center gap-3">
            {status === 'authenticated' && user ? (
              <>
                <Link to="/profiles" className="text-sm text-accent underline">
                  {profile ? `${profile.name} · Switch profile` : 'Choose profile'}
                </Link>
                <span className="hidden text-sm text-text-muted md:inline">{user.email}</span>
                <Button variant="secondary" size="sm" onClick={onSignOut}>
                  Sign out
                </Button>
              </>
            ) : null}
            {status === 'anonymous' ? (
              <Link to="/login" className="text-sm text-accent underline">
                Sign in
              </Link>
            ) : null}
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
