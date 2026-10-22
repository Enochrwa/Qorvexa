import { safeNext } from './safe-next'

describe('safeNext', () => {
  it('keeps same-site relative paths', () => {
    expect(safeNext('/titles/abc')).toBe('/titles/abc')
    expect(safeNext('/browse?genre=drama&page=2')).toBe('/browse?genre=drama&page=2')
  })

  it.each([
    ['absolute URL', 'https://evil.example.com'],
    ['protocol-relative', '//evil.example.com'],
    ['backslash trick', '/\\evil.example.com'],
    ['javascript scheme', 'javascript:alert(1)'],
    ['no leading slash', 'evil.example.com'],
    ['control character', '/ok\nSet-Cookie: x=1'],
    ['empty', ''],
  ])('rejects %s', (_name, value) => {
    expect(safeNext(value)).toBe('/')
  })

  it('handles missing and oversized input', () => {
    expect(safeNext(null)).toBe('/')
    expect(safeNext(undefined)).toBe('/')
    expect(safeNext('/' + 'a'.repeat(600))).toBe('/')
  })
})
