import axe from 'axe-core'

/** Run axe on the rendered DOM; returns readable violation summaries (empty = pass). */
export async function axeViolations(container: Element): Promise<string[]> {
  const results = await axe.run(container, {
    // jsdom has no layout engine, so colour contrast cannot be computed here. Contrast is
    // covered by the design tokens and must be checked in a real browser.
    rules: { 'color-contrast': { enabled: false } },
  })
  return results.violations.map(
    (v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join(', ')})`,
  )
}
