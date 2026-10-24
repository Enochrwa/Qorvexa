import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import { ApiError } from '@/lib/api/errors'
import { adminKey, createAdminTitle, getAdminTitle, patchAdminTitle, type AdminTitle } from './api'
import { emptyForm, formFromTitle, toCreate, toPatch } from './mapping'
import { StatusPanel } from './StatusPanel'
import { TitleForm } from './TitleForm'

const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function NewTitlePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const create = useMutation({ mutationFn: createAdminTitle })
  useEffect(() => {
    document.title = 'New title · Studio · Qorvexa'
  }, [])
  return (
    <section className="flex flex-col gap-4">
      <Link to="/admin/titles" className="text-sm text-accent underline">
        ← All titles
      </Link>
      <h2 className="text-2xl font-semibold">New title</h2>
      <TitleForm
        mode="create"
        initial={emptyForm()}
        onCancel={() => navigate('/admin/titles')}
        onSubmit={async (values) => {
          const created = await create.mutateAsync(toCreate(values))
          await queryClient.invalidateQueries({ queryKey: adminKey })
          navigate(`/admin/titles/${created.id}`, { replace: true })
        }}
      />
    </section>
  )
}

function Missing() {
  return (
    <section className="flex flex-col items-start gap-3 py-4">
      <h2 className="text-2xl font-semibold">Title not found</h2>
      <Link to="/admin/titles" className="text-accent underline">
        Back to titles
      </Link>
    </section>
  )
}

export function EditTitlePage() {
  const { id = '' } = useParams()
  if (!ID.test(id)) return <Missing />
  return <Editor id={id} />
}

function Editor({ id }: { id: string }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: [...adminKey, id], queryFn: () => getAdminTitle(id) })
  const [saved, setSaved] = useState(false)
  const patch = useMutation({
    mutationFn: (body: ReturnType<typeof toPatch>) => patchAdminTitle(id, body),
  })

  useEffect(() => {
    document.title = query.data ? `${query.data.name} · Studio · Qorvexa` : 'Studio · Qorvexa'
  }, [query.data])

  const store = (t: AdminTitle) => queryClient.setQueryData([...adminKey, id], t)

  if (query.isPending) {
    return (
      <div role="status" aria-label="Loading title" className="flex flex-col gap-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (query.error instanceof ApiError && query.error.status === 404) return <Missing />
  if (query.isError) {
    return (
      <div role="alert" className="flex flex-col items-start gap-3 text-danger">
        <p>We could not load this title.</p>
        <Button variant="secondary" onClick={() => void query.refetch()}>
          Try again
        </Button>
      </div>
    )
  }
  const title = query.data

  return (
    <section className="flex flex-col gap-6">
      <Link to="/admin/titles" className="text-sm text-accent underline">
        ← All titles
      </Link>
      <h2 className="text-2xl font-semibold">{title.name}</h2>
      <StatusPanel
        title={title}
        onChanged={store}
        onDeleted={() => {
          queryClient.removeQueries({ queryKey: [...adminKey, id] })
          navigate('/admin/titles', { replace: true })
        }}
      />
      {saved ? (
        <p role="status" className="text-success">
          Changes saved.
        </p>
      ) : null}
      <TitleForm
        key={title.updated_at}
        mode="edit"
        initial={formFromTitle(title)}
        onCancel={() => navigate('/admin/titles')}
        onSubmit={async (values) => {
          setSaved(false)
          store(await patch.mutateAsync(toPatch(values)))
          await queryClient.invalidateQueries({ queryKey: adminKey, exact: false })
          setSaved(true)
        }}
      />
    </section>
  )
}
