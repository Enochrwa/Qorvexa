import { admin, createVerifiedUser, signIn, signOut } from './helpers'
import { expect, newDevice, test } from './fixtures'

test('a viewer cannot use the studio', async ({ page, request }) => {
  const user = await createVerifiedUser(request, 'viewer-studio')
  await signIn(page, user.email, user.password)
  await expect(page.getByRole('link', { name: 'Studio', exact: true })).toHaveCount(0)
  await page.goto('/admin/titles')
  await expect(
    page.getByRole('heading', { name: /do not have access to the studio/i }),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Titles' })).toHaveCount(0)
})

test('an admin builds a series, reorders episodes by keyboard, publishes it and viewers see it', async ({
  page,
  browser,
}) => {
  const creds = admin()
  test.skip(!creds, 'E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD not set (seed an admin first)')
  const name = `E2E Series ${Date.now()}`

  await signIn(page, creds!.email, creds!.password)
  await page.getByRole('link', { name: 'Studio', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Titles', level: 2 })).toBeVisible()

  // Create the title (it starts as a draft with the most restrictive rating).
  await page.getByRole('link', { name: 'New title' }).click()
  await expect(page.getByLabel('Maturity rating')).toHaveValue('18+')
  await page.getByLabel('Name', { exact: true }).fill(name)
  await page.getByLabel('Type').selectOption('series')
  await page.getByLabel('Maturity rating').selectOption('all')
  await page.getByLabel('Synopsis').fill('Built end to end in a real browser.')
  await page.getByLabel('Poster image address (https)').fill('https://img.example.com/e2e.jpg')
  await page.getByRole('checkbox', { name: 'Drama' }).check()
  await page.getByRole('button', { name: 'Create title' }).click()
  await expect(page.getByRole('heading', { level: 2, name })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Publishing' }).getByText('draft')).toBeVisible()

  // Anonymous viewers cannot see a draft.
  const viewer = await newDevice(browser)
  await viewer.page.goto('/browse')
  await expect(viewer.page.getByRole('heading', { name: 'Browse' })).toBeVisible()
  await expect(viewer.page.getByRole('link', { name: new RegExp(name) })).toHaveCount(0)

  // Seasons and episodes.
  await page.getByRole('button', { name: 'Add season' }).click()
  await page.getByLabel('Season name (optional)').fill('One')
  await page.getByRole('button', { name: 'Create season' }).click()
  const season = page.getByRole('article', { name: 'Season 1: One' })
  for (const ep of ['Alpha', 'Bravo', 'Charlie']) {
    await season.getByRole('button', { name: /Add episode to/ }).click()
    await page.getByLabel('Episode name').fill(ep)
    await page.getByLabel('Runtime minutes').fill('40')
    await page.getByLabel('Published (viewers can see this episode)').check()
    await page.getByRole('button', { name: 'Create episode' }).click()
    await expect(season.getByText(ep, { exact: false }).first()).toBeVisible()
  }
  const order = () =>
    season
      .getByRole('listitem')
      .evaluateAll((els) =>
        els.map((e) => (e.textContent ?? '').match(/(Alpha|Bravo|Charlie)/)?.[1]),
      )
  await expect.poll(order).toEqual(['Alpha', 'Bravo', 'Charlie'])

  // Reorder with the keyboard only: focus "Move Alpha down" and press Enter twice.
  await season.getByRole('button', { name: 'Move Alpha down' }).focus()
  await page.keyboard.press('Enter')
  await expect.poll(order).toEqual(['Bravo', 'Alpha', 'Charlie'])
  await expect(season.getByRole('button', { name: 'Move Alpha down' })).toBeFocused() // focus stays on the control
  await page.keyboard.press('Enter')
  await expect.poll(order).toEqual(['Bravo', 'Charlie', 'Alpha'])
  await expect(page.getByText('Moved Alpha down to position 3 of 3.')).toBeAttached() // announced to screen readers

  // Publish; now viewers see it, with episodes in the new order.
  await page
    .getByRole('region', { name: 'Publishing' })
    .getByRole('button', { name: 'Publish' })
    .click()
  await expect(page.getByRole('region', { name: 'Publishing' }).getByText('live')).toBeVisible()
  await viewer.page.goto('/browse')
  await viewer.page.getByRole('link', { name: new RegExp(name) }).click()
  await expect(viewer.page.getByRole('heading', { level: 1, name })).toBeVisible()
  const viewerOrder = await viewer.page.getByRole('heading', { level: 3 }).allTextContents()
  expect(viewerOrder.map((t) => t.match(/(Alpha|Bravo|Charlie)/)?.[1])).toEqual([
    'Bravo',
    'Charlie',
    'Alpha',
  ])
  await viewer.page.reload()
  await expect(viewer.page.getByRole('heading', { level: 1, name })).toBeVisible()

  // A published title cannot be deleted; unpublish hides it again, then delete is allowed.
  await expect(page.getByRole('button', { name: 'Delete title' })).toBeDisabled()
  await page
    .getByRole('region', { name: 'Publishing' })
    .getByRole('button', { name: 'Unpublish' })
    .click()
  await viewer.page.reload()
  await expect(
    viewer.page.getByRole('heading', { name: 'This title is not available' }),
  ).toBeVisible()
  await page
    .getByRole('region', { name: 'Publishing' })
    .getByRole('button', { name: 'Delete title' })
    .click()
  await page
    .getByRole('region', { name: 'Publishing' })
    .getByRole('button', { name: 'Yes, delete' })
    .click()
  await expect(page).toHaveURL(/\/admin\/titles$/)
  await expect(page.getByRole('link', { name })).toHaveCount(0)
  await viewer.context.close()
  await signOut(page)
})

test('an embargoed title stays hidden until its time', async ({ page, browser }) => {
  const creds = admin()
  test.skip(!creds, 'E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD not set (seed an admin first)')
  const name = `E2E Embargo ${Date.now()}`
  await signIn(page, creds!.email, creds!.password)
  await page.goto('/admin/titles/new')
  await page.getByLabel('Name', { exact: true }).fill(name)
  await page.getByLabel('Maturity rating').selectOption('all')
  await page.getByLabel('Synopsis').fill('Scheduled.')
  await page.getByLabel('Poster image address (https)').fill('https://img.example.com/e2e.jpg')
  await page.getByRole('button', { name: 'Create title' }).click()
  const panel = page.getByRole('region', { name: 'Publishing' })
  const later = new Date(Date.now() + 3_600_000)
  const local = new Date(later.getTime() - later.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16)
  await panel.getByLabel(/Publish at/).fill(local)
  await panel.getByRole('button', { name: 'Publish' }).click()
  await expect(panel.getByText('scheduled')).toBeVisible()
  await expect(panel.getByText(/Hidden from viewers until/)).toBeVisible()

  const viewer = await newDevice(browser)
  await viewer.page.goto('/browse')
  await expect(viewer.page.getByRole('heading', { name: 'Browse' })).toBeVisible()
  await expect(viewer.page.getByRole('link', { name: new RegExp(name) })).toHaveCount(0)
  await viewer.context.close()

  await panel.getByRole('button', { name: 'Unpublish' }).click()
  await panel.getByRole('button', { name: 'Delete title' }).click()
  await panel.getByRole('button', { name: 'Yes, delete' }).click()
  await expect(page).toHaveURL(/\/admin\/titles$/)
})
