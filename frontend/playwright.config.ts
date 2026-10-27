import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests run against a real stack: built frontend, API, Postgres, Redis and Mailpit.
 * See docs/devops/e2e.md. `E2E_CHROMIUM_PATH` lets a machine without Playwright's browser
 * download use an existing Chromium.
 */
const executablePath = process.env.E2E_CHROMIUM_PATH || undefined

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: false,
  workers: 1, // tests share one database and one IP-based rate limiter
  timeout: 45_000,
  expect: { timeout: 8_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions: {
      executablePath,
      args: executablePath ? ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] : [],
    },
  },
  projects: [
    {
      name: 'desktop',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          executablePath,
          args: executablePath ? ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] : [],
        },
      },
    },
    {
      // Mobile-first product: re-run the read-only journeys on a phone-sized viewport.
      name: 'mobile',
      testMatch: /(catalog|a11y)\.spec\.ts/,
      use: {
        ...devices['Pixel 7'],
        launchOptions: {
          executablePath,
          args: executablePath ? ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] : [],
        },
      },
    },
  ],
})
