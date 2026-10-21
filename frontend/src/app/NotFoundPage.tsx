import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="flex flex-col gap-2">
      <h1 className="text-3xl font-semibold">Page not found</h1>
      <Link to="/" className="text-accent underline">
        Back to home
      </Link>
    </section>
  )
}
