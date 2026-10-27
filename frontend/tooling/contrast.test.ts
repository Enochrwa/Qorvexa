// @vitest-environment node
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const css = readFileSync(path.resolve(__dirname, '../src/styles/index.css'), 'utf8')

/**
 * WCAG AA needs 4.5:1 for normal text. jsdom cannot compute contrast, so check the design
 * tokens themselves; the Playwright accessibility spec checks the rendered pages.
 */
const token = (name: string): string => {
  const m = css.match(new RegExp(`--color-${name}:\\s*(#[0-9a-fA-F]{6})`))
  if (!m?.[1]) throw new Error(`token --color-${name} not found`)
  return m[1]
}

const channel = (c: number) =>
  c / 255 <= 0.03928 ? c / 255 / 12.92 : ((c / 255 + 0.055) / 1.055) ** 2.4
const luminance = (hex: string) => {
  const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(hex.slice(i, i + 2), 16)))
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!
}
export const contrast = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi! + 0.05) / (lo! + 0.05)
}

const SURFACES = ['bg', 'surface-1', 'surface-2', 'surface-3']
const AA = 4.5

describe('design tokens meet WCAG AA contrast', () => {
  it('computes known ratios correctly', () => {
    expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 0)
    expect(contrast('#ffffff', '#ffffff')).toBeCloseTo(1, 5)
  })

  it.each(['text', 'text-muted', 'accent', 'accent-hover', 'danger', 'success', 'warning'])(
    '%s text is readable on every surface',
    (name) => {
      for (const surface of SURFACES) {
        expect(
          contrast(token(name), token(surface)),
          `${name} on ${surface}`,
        ).toBeGreaterThanOrEqual(AA)
      }
    },
  )

  it('white text on the filled accent button, including hover', () => {
    expect(contrast('#ffffff', token('accent-solid'))).toBeGreaterThanOrEqual(AA)
    expect(contrast('#ffffff', token('accent-solid-hover'))).toBeGreaterThanOrEqual(AA)
  })

  it('white text on the secondary button surfaces', () => {
    for (const bg of ['surface-2', 'surface-3']) {
      expect(contrast(token('text'), token(bg)), `text on ${bg}`).toBeGreaterThanOrEqual(AA)
    }
  })
})
