import { Link, Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-surface-2 bg-surface-1">
        <nav aria-label="Primary" className="mx-auto flex h-14 max-w-6xl items-center px-4">
          <Link to="/" className="text-xl font-bold tracking-tight text-accent">
            Qorvexa
          </Link>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
