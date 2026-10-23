import { cn } from '@/lib/cn'

// Fixed palette (enough contrast for the white initial); avatars are preset keys, not uploads.
const COLORS = [
  '#b91c1c',
  '#c2410c',
  '#a16207',
  '#4d7c0f',
  '#047857',
  '#0f766e',
  '#0369a1',
  '#1d4ed8',
  '#6d28d9',
  '#a21caf',
  '#be185d',
  '#475569',
]

export function avatarColor(avatar: string): string {
  const n = Number(avatar.replace('avatar-', ''))
  return COLORS[(Number.isInteger(n) && n >= 1 ? n - 1 : 0) % COLORS.length] ?? COLORS[0]!
}

export function Avatar({
  avatar,
  name,
  className,
}: {
  avatar: string
  name: string
  className?: string
}) {
  return (
    <span
      aria-hidden="true"
      style={{ backgroundColor: avatarColor(avatar) }}
      className={cn(
        'flex h-20 w-20 items-center justify-center rounded-lg text-3xl font-bold text-white',
        className,
      )}
    >
      {name.trim().charAt(0).toUpperCase() || '?'}
    </span>
  )
}
