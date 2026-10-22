import type { ReactNode } from 'react'

export function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6 py-8">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <div className="rounded-lg border border-surface-3 bg-surface-1 p-6">{children}</div>
    </div>
  )
}

export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <p
      role="alert"
      className="rounded-md border border-danger/40 bg-danger/10 p-3 text-sm text-danger"
    >
      {message}
    </p>
  )
}

export function Notice({ children }: { children: ReactNode }) {
  return (
    <p role="status" className="rounded-md border border-surface-3 bg-surface-2 p-3 text-sm">
      {children}
    </p>
  )
}
