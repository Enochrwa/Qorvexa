import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { PROFILES } from './fixtures'

export const API = 'http://localhost:8000/api/v1'

/**
 * Baseline handlers for calls the app shell makes whenever a user is signed in.
 * Tests override them with server.use(); everything else must be mocked explicitly
 * (unhandled requests fail loudly).
 */
export const server = setupServer(http.get(`${API}/profiles`, () => HttpResponse.json(PROFILES)))
