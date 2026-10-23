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
