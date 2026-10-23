import { formatRuntime, parseFilters, ratingLabel, safeImageUrl, toSearchParams } from './params'

const q = (s: string) => new URLSearchParams(s)

describe('parseFilters', () => {
  it('reads valid filters', () => {
    expect(parseFilters(q('type=series&genre=sci-fi&sort=name'))).toEqual({
      type: 'series',
      genre: 'sci-fi',
      sort: 'name',
    })
  })

  it('uses defaults when nothing is given', () => {
    expect(parseFilters(q(''))).toEqual({ type: null, genre: null, sort: 'added' })
  })

  it.each([
    ['unknown type', 'type=book'],
    ['upper-case type', 'type=MOVIE'],
    ['bad genre characters', 'genre=Bad%20Slug!'],
    ['genre with path', 'genre=../../etc'],
    ['over-long genre', 'genre=' + 'a'.repeat(61)],
    ['unknown sort', 'sort=popular'],
    ['injection attempt', 'type=movie%26limit%3D9999'],
  ])('ignores %s', (_n, query) => {
    const f = parseFilters(q(query))
    expect(f.genre).toBeNull()
    expect(f.sort).toBe('added')
    expect(f.type).toBeNull()
  })
})

describe('toSearchParams', () => {
  it('omits defaults and round-trips', () => {
    expect(toSearchParams({ type: null, genre: null, sort: 'added' }).toString()).toBe('')
    const f = { type: 'movie', genre: 'drama', sort: 'year' } as const
    expect(parseFilters(toSearchParams(f))).toEqual(f)
  })
})

describe('formatRuntime', () => {
  it.each([
    [null, null],
    [undefined, null],
    [0, null],
    [-5, null],
    [30, '1 min'],
    [2700, '45 min'],
    [3600, '1 h'],
    [3900, '1 h 5 min'],
    [6300, '1 h 45 min'],
  ])('%s -> %s', (input, expected) => {
    expect(formatRuntime(input as number | null | undefined)).toBe(expected)
  })
})

describe('safeImageUrl', () => {
  it('allows only https', () => {
    expect(safeImageUrl('https://img.example.com/a.jpg')).toBe('https://img.example.com/a.jpg')
    for (const bad of [
      'http://img.example.com/a.jpg',
      'javascript:alert(1)',
      'data:image/png;base64,AAAA',
      '//img.example.com/a.jpg',
      '',
      null,
      undefined,
    ]) {
      expect(safeImageUrl(bad)).toBeNull()
    }
  })
})

it('ratingLabel', () => {
  expect(ratingLabel('all')).toBe('All ages')
  expect(ratingLabel('16+')).toBe('16+')
})
