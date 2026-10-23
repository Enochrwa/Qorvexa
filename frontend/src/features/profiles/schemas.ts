import { z } from 'zod'
import { AVATARS, LANGUAGES, MATURITY, SUBTITLE_SIZES } from './options'

export const profileSchema = z.object({
  name: z.string().trim().min(1, 'Enter a name').max(40, 'Use at most 40 characters'),
  avatar: z.enum(AVATARS as [string, ...string[]]),
  language: z.enum(LANGUAGES.map((l) => l.code) as [string, ...string[]]),
  maturity_limit: z.enum(MATURITY.map((m) => m.value) as [string, ...string[]]),
  autoplay_next: z.boolean(),
  data_saver: z.boolean(),
  subtitles_enabled: z.boolean(),
  subtitles_size: z.enum(SUBTITLE_SIZES),
})

export type ProfileFormValues = z.infer<typeof profileSchema>
