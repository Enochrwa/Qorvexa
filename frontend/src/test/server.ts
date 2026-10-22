import { setupServer } from 'msw/node'

export const server = setupServer()
export const API = 'http://localhost:8000/api/v1'
