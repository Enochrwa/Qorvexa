import type { Me } from '@/lib/api/session'

const RANK: Record<string, number> = { viewer: 0, editor: 1, admin: 2 }

/** UI convenience only. The server enforces roles on every admin endpoint. */
export function hasRole(
  user: Me | null | undefined,
  minimum: 'viewer' | 'editor' | 'admin',
): boolean {
  return user != null && (RANK[user.role] ?? -1) >= (RANK[minimum] ?? Infinity)
}
