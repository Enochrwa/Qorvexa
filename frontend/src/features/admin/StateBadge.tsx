import { cn } from '@/lib/cn'

const STYLES: Record<string, string> = {
  live: 'bg-success/15 text-success',
  scheduled: 'bg-warning/15 text-warning',
  expired: 'bg-surface-3 text-text-muted',
  draft: 'bg-surface-3 text-text',
  archived: 'bg-surface-3 text-text-muted',
}

/** Text label, not colour alone. */
export function StateBadge({ state }: { state: string }) {
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-xs font-medium capitalize',
        STYLES[state] ?? STYLES.draft,
      )}
    >
      {state}
    </span>
  )
}
