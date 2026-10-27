import AxeBuilder from '@axe-core/playwright'
import type { Page } from '@playwright/test'
import { admin, createVerifiedUser, signIn } from './helpers'
import { expect, test } from './fixtures'

/** Real-browser axe run, including colour contrast (which jsdom cannot compute). */
async function audit(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  const summary = results.violations.map(
    (v) =>
      `${v.id} (${v.impact}): ${v.help}\n   ${v.nodes
        .slice(0, 4)
        .map((n) => `${n.target.join(' ')} :: ${(n.any[0]?.message ?? '').slice(0, 110)}`)
        .join('\n   ')}`,
  )
  expect(summary, summary.join('\n')).toEqual([])
}

test('public pages have no accessibility violations', async ({ page }) => {
  for (const [path, heading] of [
    ['/login', 'Sign in'],
    ['/register', 'Create your account'],
    ['/forgot-password', 'Reset your password'],
    ['/browse', 'Browse'],
    ['/titles/sample-market-day', '[Sample] Market Day'],
  ] as const) {
    await page.goto(path)
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible()
    await page
      .locator('[aria-label="Loading titles"]')
      .waitFor({ state: 'detached' })
      .catch(() => undefined)
    await audit(page)
  }
})

test('signed-in pages have no accessibility violations', async ({ page, request }) => {
  const user = await createVerifiedUser(request, 'a11y')
  await signIn(page, user.email, user.password)
  for (const [path, heading] of [
    ['/profiles', 'Who is watching?'],
    ['/profiles/manage', 'Manage profiles'],
  ] as const) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    await audit(page)
  }
  await page.getByRole('button', { name: 'Add profile' }).click()
  await expect(page.getByLabel('Name')).toBeVisible()
  await audit(page)
})

test('studio pages have no accessibility violations', async ({ page }) => {
  const creds = admin()
  test.skip(!creds, 'E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD not set (seed an admin first)')
  await signIn(page, creds!.email, creds!.password)
  await page.goto('/admin/titles')
  await expect(page.getByRole('heading', { name: 'Titles', level: 2 })).toBeVisible()
  await expect(page.getByRole('table').or(page.getByText(/No titles/))).toBeVisible()
  await audit(page)
  await page.goto('/admin/titles/new')
  await expect(page.getByRole('heading', { name: 'New title' })).toBeVisible()
  await page.getByRole('button', { name: 'Add person' }).click()
  await audit(page)
})
