import { createVerifiedUser, signIn } from './helpers'
import { expect, test } from './fixtures'

/**
 * Refresh tokens rotate. If the server rotates the token but the response never reaches the
 * browser (connection drops, or the page is reloaded mid-request), the browser still holds
 * the old token. That must not be treated as theft and sign the user out.
 */
test('a lost refresh response does not sign the user out', async ({ page, request, clientIp }) => {
  const user = await createVerifiedUser(request, 'lost-refresh')
  await signIn(page, user.email, user.password)

  let dropped = 0
  await page.route('**/api/v1/auth/refresh', async (route) => {
    if (dropped++ === 0) {
      // The server processes (and rotates) the token, but the browser never hears back.
      const cookie = (await page.context().cookies()).find((c) => c.name === 'refresh_token')
      await fetch(route.request().url(), {
        method: 'POST',
        headers: {
          cookie: `refresh_token=${cookie?.value}`,
          'x-qorvexa-client': 'web',
          'x-forwarded-for': clientIp,
        },
      })
      return route.abort('failed')
    }
    return route.continue()
  })

  await page.reload()
  await expect.poll(() => dropped).toBeGreaterThanOrEqual(1) // the app has asked for a refresh
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()

  // And the session is genuinely alive afterwards, not just for this page load.
  await page.reload()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
})

test('reloading while the session is still being restored does not sign the user out', async ({
  page,
  request,
}) => {
  const user = await createVerifiedUser(request, 'quick-reload')
  await signIn(page, user.email, user.password)
  // Reload several times in quick succession, without waiting for the app to settle.
  // (Chromium can refuse a reload that lands mid-navigation; that is the browser, not the app.)
  for (let i = 0; i < 4; i++) await page.reload({ waitUntil: 'commit' }).catch(() => undefined)
  await page.waitForLoadState('domcontentloaded')
  await page.reload()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
})
