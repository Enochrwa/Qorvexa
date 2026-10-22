import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Skeleton } from '@/components/Skeleton'
import { useSession } from '@/lib/api/session'

function Loading() {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-3 py-8">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-32 w-full" />
    </div>
  )
}

/** Routes that need a signed-in user. Anonymous visitors go to /login and come back after. */
export function RequireAuth() {
  const status = useSession((s) => s.status)
  const location = useLocation()
  if (status === 'loading') return <Loading />
  if (status === 'anonymous') {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return <Outlet />
}

/** Login and register pages: signed-in users are sent home instead. */
export function RedirectIfAuthed() {
  const status = useSession((s) => s.status)
  if (status === 'loading') return <Loading />
  if (status === 'authenticated') return <Navigate to="/" replace />
  return <Outlet />
}
