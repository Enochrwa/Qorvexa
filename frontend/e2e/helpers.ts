import { expect, type APIRequestContext, type Page } from '@playwright/test'

export const API = process.env.E2E_API_URL ?? 'http://localhost:8000'
export const MAILPIT = process.env.MAILPIT_URL ?? 'http://localhost:8025'
export const PASSWORD = 'e2e-passphrase-long-1'

export const uniqueEmail = (tag: string) =>
  `e2e-${tag}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`

type MailMessage = { ID: string; Created: string }

/** Wait for a mail to `to` containing a link with `path`, and return that link. */
export async function mailLink(
  request: APIRequestContext,
  to: string,
  path: string,
): Promise<string> {
  const deadline = Date.now() + 15_000
  while (Date.now() < deadline) {
    const search = await request.get(`${MAILPIT}/api/v1/search`, { params: { query: `to:${to}` } })
    const { messages = [] } = (await search.json()) as { messages?: MailMessage[] }
    for (const m of messages) {
      const detail = (await (await request.get(`${MAILPIT}/api/v1/message/${m.ID}`)).json()) as {
        Text: string
      }
      const match = detail.Text.match(new RegExp(`https?://\\S+${path}\\?token=[\\w-]+`))
      if (match) return match[0]
    }
    await new Promise((r) => setTimeout(r, 250))
  }
  throw new Error(`No email with a ${path} link arrived for ${to}`)
}

/** Create a verified account through the API (not the UI), for tests that are not about sign up. */
export async function createVerifiedUser(request: APIRequestContext, tag: string) {
  const email = uniqueEmail(tag)
  const reg = await request.post(`${API}/api/v1/auth/register`, {
    data: { email, password: PASSWORD },
  })
  expect(
    reg.status(),
    'register (a 429 means the rate limit is exhausted: flush Redis, see docs/devops/e2e.md)',
  ).toBe(202)
  const link = await mailLink(request, email, '/verify-email')
  const token = new URL(link).searchParams.get('token')
  const ok = await request.post(`${API}/api/v1/auth/verify-email`, { data: { token } })
  expect(ok.status()).toBe(204)
  return { email, password: PASSWORD }
}

export async function signIn(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
}

export async function signOut(page: Page) {
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
}

export function shared() {
  const email = process.env.E2E_VIEWER_EMAIL
  const password = process.env.E2E_VIEWER_PASSWORD
  if (!email || !password) throw new Error('Shared viewer missing: global setup did not run')
  return { email, password }
}

export const admin = () => {
  const email = process.env.E2E_ADMIN_EMAIL
  const password = process.env.E2E_ADMIN_PASSWORD
  return email && password ? { email, password } : null
}
