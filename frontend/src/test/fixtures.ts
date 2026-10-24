export const ME = { id: 'u1', email: 'viewer@example.com', role: 'viewer', email_verified: true }

export const PROFILES = [
  {
    id: 'p1',
    name: 'Alex',
    avatar: 'avatar-2',
    language: 'en',
    maturity_limit: '18+',
    autoplay_next: true,
    data_saver: false,
    subtitle_prefs: {},
  },
  {
    id: 'p2',
    name: 'Kids',
    avatar: 'avatar-5',
    language: 'rw',
    maturity_limit: '7+',
    autoplay_next: true,
    data_saver: true,
    subtitle_prefs: { enabled: true, size: 'large' },
  },
]

export function item(n: number, overrides: Record<string, unknown> = {}) {
  return {
    id: `t${n}`,
    slug: `title-${n}`,
    type: 'movie',
    name: `Title ${n}`,
    release_year: 2020 + (n % 5),
    maturity_rating: '13+',
    language: 'en',
    poster_url: null,
    genres: [{ name: 'Drama', slug: 'drama' }],
    ...overrides,
  }
}

export const GENRES = [
  { name: 'Comedy', slug: 'comedy' },
  { name: 'Drama', slug: 'drama' },
]

export const DETAIL = {
  ...item(1, {
    name: 'The Long Road',
    slug: 'the-long-road',
    poster_url: 'https://img.example.com/p.jpg',
  }),
  original_name: null,
  synopsis: 'A journey across the country.',
  country: 'RW',
  backdrop_url: 'https://img.example.com/b.jpg',
  downloads_enabled: false,
  season_count: 0,
  cast: [
    { name: 'Dee Rector', slug: 'dee-rector', role: 'director' },
    { name: 'Amy Lead', slug: 'amy-lead', role: 'actor' },
    { name: 'Zed Actor', slug: 'zed-actor', role: 'actor' },
  ],
}

export const SEASONS = [
  {
    number: 1,
    name: 'First',
    synopsis: null,
    episodes: [
      {
        id: 'e1',
        number: 1,
        name: 'Pilot',
        synopsis: 'It begins.',
        runtime_seconds: 2700,
        air_date: null,
      },
      {
        id: 'e2',
        number: 2,
        name: 'Second',
        synopsis: null,
        runtime_seconds: 3900,
        air_date: null,
      },
    ],
  },
  {
    number: 2,
    name: null,
    synopsis: null,
    episodes: [
      {
        id: 'e3',
        number: 1,
        name: 'Return',
        synopsis: null,
        runtime_seconds: null,
        air_date: null,
      },
    ],
  },
]

export const EDITOR = {
  id: 'u2',
  email: 'editor@example.com',
  role: 'editor',
  email_verified: true,
}
export const ADMIN_USER = {
  id: 'u3',
  email: 'admin@example.com',
  role: 'admin',
  email_verified: true,
}

export const TITLE_ID = '0b1f6a52-3c0e-4a52-9b0a-1b5d9f0c1a11'

export function adminItem(n: number, overrides: Record<string, unknown> = {}) {
  return {
    id: `0b1f6a52-3c0e-4a52-9b0a-${String(n).padStart(12, '0')}`,
    slug: `title-${n}`,
    type: 'movie',
    name: `Title ${n}`,
    status: 'draft',
    state: 'draft',
    maturity_rating: '13+',
    release_year: 2021,
    publish_at: null,
    available_until: null,
    updated_at: '2026-10-22T10:00:00Z',
    ...overrides,
  }
}

export const ADMIN_TITLE = {
  ...adminItem(1, { id: TITLE_ID, slug: 'the-long-road', name: 'The Long Road' }),
  original_name: 'Original',
  synopsis: 'A journey.',
  language: 'en',
  country: 'RW',
  poster_url: 'https://img.example.com/p.jpg',
  backdrop_url: null,
  downloads_enabled: false,
  created_at: '2026-10-20T10:00:00Z',
  genres: ['drama'],
  cast: [
    { name: 'Dee Rector', role: 'director', billing_order: 0 },
    { name: 'Amy Lead', role: 'actor', billing_order: 1 },
  ],
}
