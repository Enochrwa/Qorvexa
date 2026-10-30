import { test as base, expect, type Browser, type BrowserContext } from '@playwright/test'

/**
 * The API limits sign-ins and sign-ups per client address. One machine running a whole suite
 * would trip those limits and cause misleading failures, so every test presents its own
 * address through X-Forwarded-For. This needs the API to run with TRUSTED_PROXY_COUNT=1
 * (docs/devops/e2e.md); it also exercises that setting for real.
 */
export const randomIp = () => {
  const n = () => 1 + Math.floor(Math.random() * 253)
  return `10.${n()}.${n()}.${n()}`
}

export async function isolate(context: BrowserContext, ip: string = randomIp()) {
  // Added after the browser's CORS checks, so it does not need to be an allowed header.
  await context.route(/\/api\/v1\//, (route) =>
    route.continue({ headers: { ...route.request().headers(), 'x-forwarded-for': ip } }),
  )
  return ip
}

/** A second, independent "device" (own cookies and storage, own client address). */
export async function newDevice(browser: Browser) {
  const context = await browser.newContext()
  await isolate(context)
  return { context, page: await context.newPage() }
}

export const test = base.extend<{ clientIp: string }>({
  // A strict Content-Security-Policy (served with the app) must never block our own pages.
  page: async ({ page }, use) => {
    const violations: string[] = []
    page.on('console', (m) => {
      if (/Content Security Policy|Refused to (load|apply|execute|connect)/i.test(m.text()))
        violations.push(m.text())
    })
    await use(page)
    expect(violations, 'Content-Security-Policy violations in the browser console').toEqual([])
  },
  clientIp: async ({}, use) => use(randomIp()),
  context: async ({ context, clientIp }, use) => {
    await isolate(context, clientIp)
    await use(context)
  },
  request: async ({ playwright, clientIp }, use) => {
    const ctx = await playwright.request.newContext({
      extraHTTPHeaders: { 'x-forwarded-for': clientIp },
    })
    await use(ctx)
    await ctx.dispose()
  },
})

export { expect }
