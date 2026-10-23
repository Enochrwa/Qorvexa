import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Skeleton } from '@/components/Skeleton'
import { useCurrentProfile } from './hooks'

/** Inside RequireAuth: sends the user to the picker until a profile is chosen. */
export function RequireProfile() {
  const { profile, loading, profiles, error } = useCurrentProfile()
  const location = useLocation()
  if (loading) {
    return (
      <div role="status" aria-label="Loading" className="py-8">
        <Skeleton className="h-8 w-48" />
      </div>
    )
  }
  if (error) {
    return (
      <p role="alert" className="py-8 text-danger">
        We could not load your profiles. Please reload the page.
      </p>
    )
  }
  // A lone profile is selected by useCurrentProfile on the next render; avoid a redirect flash.
  if (!profile && profiles.length === 1) return null
  if (!profile) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/profiles?next=${next}`} replace />
  }
  return <Outlet />
}
