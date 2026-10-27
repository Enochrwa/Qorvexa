import { request } from '@playwright/test'
import { randomIp } from './fixtures'
import { API, createVerifiedUser, MAILPIT } from './helpers'

/** One shared viewer for read-mostly tests, created once so we stay under the sign-up rate limit. */
export default async function globalSetup() {
  const ctx = await request.newContext({ extraHTTPHeaders: { 'x-forwarded-for': randomIp() } })
  for (const [name, url] of [
    ['API', `${API}/ready`],
    ['Mailpit', `${MAILPIT}/api/v1/info`],
  ] as const) {
    const res = await ctx.get(url).catch(() => null)
    if (!res?.ok())
      throw new Error(
        `${name} is not reachable at ${url}. Start the stack first (docs/devops/e2e.md).`,
      )
  }
  const user = await createVerifiedUser(ctx, 'shared')
  process.env.E2E_VIEWER_EMAIL = user.email
  process.env.E2E_VIEWER_PASSWORD = user.password
  await ctx.dispose()
}
