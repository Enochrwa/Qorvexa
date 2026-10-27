import { expect, newDevice, test } from './fixtures'
import {
  createVerifiedUser,
  mailLink,
  PASSWORD,
  shared,
  signIn,
  signOut,
  uniqueEmail,
} from './helpers'

test('sign up by email link, stay signed in across reloads, sign out for good', async ({
  page,
  request,
}) => {
  const email = uniqueEmail('signup')
  await page.goto('/register')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByLabel('Confirm password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByRole('heading', { name: 'Check your email' })).toBeVisible()

  // Signing in before verifying is refused with a helpful message.
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('alert')).toContainText('verify your email first')

  const link = await mailLink(request, email, '/verify-email')
  await page.goto(link)
  await expect(page.getByText('Your email is verified')).toBeVisible()
  expect(page.url()).not.toContain('token=') // the token is stripped from the address bar

  await signIn(page, email, PASSWORD)
  await expect(page).toHaveURL(/\/browse$/)
  await expect(page.getByText(email)).toBeVisible()

  // The in-memory token is gone after a reload; the httpOnly cookie restores the session.
  await page.reload()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
  await expect(page.getByText(email)).toBeVisible()
  const stored = await page.evaluate(
    () => JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }),
  )
  expect(stored).not.toMatch(/eyJ/) // no JWT in browser storage (a JWT always starts with eyJ)
  const cookies = await page.context().cookies()
  const refresh = cookies.find((c) => c.name === 'refresh_token')
  expect(refresh?.httpOnly).toBe(true)

  await signOut(page)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible() // still signed out
})

test('a wrong password gives a safe message and no session', async ({ page }) => {
  const { email } = shared()
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill('definitely-wrong-password')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('alert')).toHaveText('Incorrect email or password.')
  await expect(page.getByRole('button', { name: 'Sign out' })).toHaveCount(0)
})

test('protected pages send visitors to sign in and bring them back', async ({ page }) => {
  const { email, password } = shared()
  await page.goto('/profiles/manage')
  await expect(page).toHaveURL(/\/login\?next=%2Fprofiles%2Fmanage$/)
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/profiles\/manage$/)
  await expect(page.getByRole('heading', { name: 'Manage profiles' })).toBeVisible()
})

test('a malicious ?next cannot leave the site', async ({ page }) => {
  const { email, password } = shared()
  await page.goto('/login?next=https%3A%2F%2Fevil.example.com')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/localhost:\d+\/browse$/)
})

test('password reset by email: new password works, old one does not, other sessions end', async ({
  page,
  browser,
  request,
}) => {
  const user = await createVerifiedUser(request, 'reset')

  // A second device stays signed in until the reset happens.
  const { context: other, page: otherPage } = await newDevice(browser)
  await signIn(otherPage, user.email, user.password)

  await page.goto('/forgot-password')
  await page.getByLabel('Email').fill(user.email)
  await page.getByRole('button', { name: 'Send reset link' }).click()
  await expect(page.getByRole('status')).toContainText('If an account exists')

  const link = await mailLink(request, user.email, '/reset-password')
  await page.goto(link)
  expect(page.url()).not.toContain('token=')
  const next = 'a-brand-new-passphrase-2'
  await page.getByLabel('New password', { exact: true }).fill(next)
  await page.getByLabel('Confirm new password').fill(next)
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByRole('status')).toContainText('signed out everywhere')

  await page.goto('/login')
  await page.getByLabel('Email').fill(user.email)
  await page.getByLabel('Password').fill(user.password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('alert')).toHaveText('Incorrect email or password.')
  await signIn(page, user.email, next)

  // The other device's session was revoked: reloading shows the signed-out state.
  await otherPage.reload()
  await expect(
    otherPage
      .getByRole('heading', { name: 'Sign in' })
      .or(otherPage.getByRole('link', { name: 'Sign in' })),
  ).toBeVisible()
  await expect(otherPage.getByRole('button', { name: 'Sign out' })).toHaveCount(0)
  await other.close()
})

test('the reset link works only once', async ({ page, request }) => {
  const user = await createVerifiedUser(request, 'once')
  await request.post('http://localhost:8000/api/v1/auth/password/forgot', {
    data: { email: user.email },
  })
  const link = await mailLink(request, user.email, '/reset-password')
  await page.goto(link)
  await page.getByLabel('New password', { exact: true }).fill('first-new-passphrase-3')
  await page.getByLabel('Confirm new password').fill('first-new-passphrase-3')
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByRole('status')).toContainText('signed out everywhere')

  await page.goto(link)
  await page.getByLabel('New password', { exact: true }).fill('second-new-passphrase-4')
  await page.getByLabel('Confirm new password').fill('second-new-passphrase-4')
  await page.getByRole('button', { name: 'Change password' }).click()
  await expect(page.getByRole('alert')).toContainText('invalid or has expired')
})
