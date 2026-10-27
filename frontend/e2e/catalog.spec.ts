import { createVerifiedUser, signIn, signOut } from './helpers'
import { expect, test } from './fixtures'

// Sample titles come from `make seed` (docs/devops/e2e.md):
//   all: Market Day (movie) | 7+: Lake Stories (series) | 13+: The Long Road (movie) | 16+: Night Shift (series)
const link = (page: import('@playwright/test').Page, name: string) =>
  page.getByRole('link', { name: new RegExp(name) })

test('anonymous visitors browse a safe default catalog, filter it and open a title', async ({
  page,
}) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/browse$/)
  await expect(link(page, 'Market Day')).toBeVisible()
  await expect(link(page, 'The Long Road')).toBeVisible()
  await expect(link(page, 'Night Shift')).toHaveCount(0) // 16+ is hidden from anonymous visitors

  await page.getByLabel('Type').selectOption('series')
  await expect(page).toHaveURL(/type=series/)
  await expect(link(page, 'Lake Stories')).toBeVisible()
  await expect(link(page, 'Market Day')).toHaveCount(0)

  await link(page, 'Lake Stories').click()
  await expect(page.getByRole('heading', { level: 1, name: '[Sample] Lake Stories' })).toBeVisible()
  await expect(page.getByText('Rated 7+')).toBeVisible()
  await expect(page.getByText('No episodes have been published yet.')).toBeVisible()
  await page.getByRole('link', { name: '← Back to browse' }).click()
  await expect(page).toHaveURL(/\/browse/)
})

test('a hidden title looks the same as a missing one', async ({ page }) => {
  await page.goto('/titles/sample-night-shift') // 16+, hidden from anonymous visitors
  await expect(page.getByRole('heading', { name: 'This title is not available' })).toBeVisible()
  await page.goto('/titles/does-not-exist')
  await expect(page.getByRole('heading', { name: 'This title is not available' })).toBeVisible()
})

test('the chosen profile decides what you can see, and is remembered', async ({
  page,
  request,
}) => {
  const user = await createVerifiedUser(request, 'profiles')
  await signIn(page, user.email, user.password)

  // The default profile is 18+ and is selected automatically when it is the only one.
  await expect(link(page, 'Night Shift')).toBeVisible()

  await page.goto('/profiles/manage')
  await page.getByRole('button', { name: 'Add profile' }).click()
  await page.getByLabel('Name').fill('Kids')
  await page.getByLabel('Maturity limit').selectOption('7+')
  await page.getByRole('button', { name: 'Create profile' }).click()
  await expect(page.getByRole('heading', { name: 'Manage profiles' })).toBeVisible()

  await page.goto('/profiles')
  await page.getByRole('button', { name: /Kids/ }).click()
  await expect(page).toHaveURL(/\/browse$/)
  await expect(link(page, 'Lake Stories')).toBeVisible() // 7+
  await expect(link(page, 'Market Day')).toBeVisible() // all ages
  await expect(link(page, 'The Long Road')).toHaveCount(0) // 13+
  await expect(link(page, 'Night Shift')).toHaveCount(0) // 16+
  await expect(page.getByRole('link', { name: /Kids · Switch profile/ })).toBeVisible()

  // The same hidden title is refused on its own page too, not just left out of the list.
  await page.goto('/titles/sample-night-shift')
  await expect(page.getByRole('heading', { name: 'This title is not available' })).toBeVisible()

  // Remembered across a reload and across signing out and back in.
  await page.goto('/browse')
  await page.reload()
  await expect(page.getByRole('link', { name: /Kids · Switch profile/ })).toBeVisible()
  await expect(link(page, 'Night Shift')).toHaveCount(0)
  await signOut(page)
  await signIn(page, user.email, user.password)
  await expect(page.getByRole('link', { name: /Kids · Switch profile/ })).toBeVisible()
  await expect(link(page, 'Night Shift')).toHaveCount(0)
})

test('a deleted profile does not leave the app stuck', async ({ page, request }) => {
  const user = await createVerifiedUser(request, 'deleted-profile')
  await signIn(page, user.email, user.password)
  await page.goto('/profiles/manage')
  await page.getByRole('button', { name: 'Add profile' }).click()
  await page.getByLabel('Name').fill('Temp')
  await page.getByRole('button', { name: 'Create profile' }).click()
  await page.goto('/profiles')
  await page.getByRole('button', { name: /Temp/ }).click()
  await expect(page.getByRole('link', { name: /Temp · Switch profile/ })).toBeVisible()

  await page.goto('/profiles/manage')
  await page.getByRole('button', { name: 'Delete Temp' }).click()
  await page.getByRole('button', { name: 'Yes, delete' }).click()
  await expect(page.getByRole('button', { name: 'Delete Temp' })).toHaveCount(0)
  await page.goto('/browse')
  await expect(link(page, 'Market Day')).toBeVisible()
  await expect(page.getByRole('link', { name: /Temp/ })).toHaveCount(0)
})
