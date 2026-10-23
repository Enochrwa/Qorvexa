import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Skeleton } from '@/components/Skeleton'
import { safeNext } from '@/features/auth/safe-next'
import { useSession } from '@/lib/api/session'
import { Avatar } from './Avatar'
import { useProfiles } from './hooks'
import { useProfile } from './store'

export function ProfilePickerPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const userId = useSession((s) => s.user?.id)
  const selectedId = useProfile((s) => s.selectedId)
  const { data: profiles, isPending, isError } = useProfiles()

  function choose(id: string) {
    if (!userId) return
    useProfile.getState().select(userId, id)
    navigate(safeNext(params.get('next')), { replace: true })
  }

  return (
    <section className="mx-auto flex max-w-3xl flex-col items-center gap-8 py-8">
      <h1 className="text-3xl font-semibold">Who is watching?</h1>
      {isPending ? (
        <div role="status" aria-label="Loading profiles" className="flex gap-4">
          <Skeleton className="h-28 w-24" />
          <Skeleton className="h-28 w-24" />
        </div>
      ) : isError ? (
        <p role="alert" className="text-danger">
          We could not load your profiles. Please try again.
        </p>
      ) : (
        <ul className="flex flex-wrap justify-center gap-6">
          {profiles.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => choose(p.id)}
                aria-current={p.id === selectedId ? 'true' : undefined}
                className="flex w-28 flex-col items-center gap-2 rounded-lg p-2 hover:bg-surface-2"
              >
                <Avatar avatar={p.avatar} name={p.name} />
                <span className="max-w-full truncate text-sm">{p.name}</span>
                <span className="text-xs text-text-muted">
                  {p.maturity_limit === 'all' ? 'All ages' : p.maturity_limit}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <Link to="/profiles/manage" className="text-accent underline">
        Manage profiles
      </Link>
    </section>
  )
}
