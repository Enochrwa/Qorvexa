export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'rw', label: 'Kinyarwanda' },
  { code: 'fr', label: 'Français' },
  { code: 'sw', label: 'Kiswahili' },
] as const

export const MATURITY = [
  { value: 'all', label: 'All ages' },
  { value: '7+', label: '7+' },
  { value: '13+', label: '13+' },
  { value: '16+', label: '16+' },
  { value: '18+', label: '18+ (everything)' },
] as const

export const AVATARS = Array.from({ length: 12 }, (_, i) => `avatar-${i + 1}`)

export const SUBTITLE_SIZES = ['small', 'medium', 'large'] as const
