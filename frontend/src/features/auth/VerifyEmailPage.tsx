import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { friendlyMessage } from '@/lib/api/errors'
import { verifyEmail } from './api'
import { AuthLayout, FormAlert, Notice } from './AuthLayout'

// Verification tokens are single-use. React StrictMode runs effects twice in development,
// so cache the request per token to guarantee exactly one call.
const attempts = new Map<string, Promise<void>>()

type State = { kind: 'working' } | { kind: 'done' } | { kind: 'failed'; message: string }

export function VerifyEmailPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  // Read the token once, then strip it from the address bar so it is not kept in history.
  const [token] = useState(() => params.get('token'))
  const [state, setState] = useState<State>(
    token
      ? { kind: 'working' }
      : { kind: 'failed', message: 'This link is invalid or has expired.' },
  )

  useEffect(() => {
    if (!token) return
    navigate('/verify-email', { replace: true })
    let request = attempts.get(token)
    if (!request) {
      request = verifyEmail(token)
      attempts.set(token, request)
    }
    request.then(
      () => setState({ kind: 'done' }),
      (err: unknown) => setState({ kind: 'failed', message: friendlyMessage(err) }),
    )
  }, [token, navigate])

  return (
    <AuthLayout title="Verify your email">
      {state.kind === 'working' && <Notice>Verifying your email…</Notice>}
      {state.kind === 'done' && (
        <div className="flex flex-col gap-4">
          <Notice>Your email is verified. You can sign in now.</Notice>
          <Link to="/login" className="text-accent underline">
            Go to sign in
          </Link>
        </div>
      )}
      {state.kind === 'failed' && (
        <div className="flex flex-col gap-4">
          <FormAlert message={state.message} />
          <Link to="/register" className="text-accent underline">
            Register again
          </Link>
        </div>
      )}
    </AuthLayout>
  )
}
