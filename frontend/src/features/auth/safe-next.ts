/**
 * Only allow same-site relative paths after login (prevents open redirects).
 * Rejects absolute URLs, protocol-relative `//host`, backslash tricks and control characters.
 */
export function safeNext(next: string | null | undefined): string {
  if (!next || next.length > 500) return '/'
  if (!next.startsWith('/') || next.startsWith('//') || next.includes('\\')) return '/'
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(next)) return '/'
  return next
}
