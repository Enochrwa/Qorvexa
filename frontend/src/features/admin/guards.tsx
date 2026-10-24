import { Link, Outlet } from 'react-router-dom'
import { useSession } from '@/lib/api/session'
import { hasRole } from './role'

/** Inside RequireAuth: only editors and admins see the studio. */
export function RequireEditor() {
  const user = useSession((s) => s.user)
  if (!hasRole(user, 'editor')) {
    return (
      <section className="flex flex-col items-start gap-3 py-8">
        <h1 className="text-2xl font-semibold">You do not have access to the studio</h1>
        <p className="text-text-muted">
          Ask an administrator to give your account the editor role.
        </p>
        <Link to="/browse" className="text-accent underline">
          Back to browse
        </Link>
      </section>
    )
  }
  return <Outlet />
}
