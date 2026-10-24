import { NavLink, Outlet } from 'react-router-dom'

export function AdminLayout() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4 border-b border-surface-2 pb-3">
        <h1 className="sr-only">Studio</h1>
        <p aria-hidden="true" className="text-lg font-semibold">
          Studio
        </p>
        <nav aria-label="Studio" className="flex gap-4 text-sm">
          <NavLink
            to="/admin/titles"
            className={({ isActive }) =>
              isActive ? 'font-semibold text-text' : 'text-accent underline'
            }
          >
            Titles
          </NavLink>
        </nav>
      </div>
      <Outlet />
    </div>
  )
}
