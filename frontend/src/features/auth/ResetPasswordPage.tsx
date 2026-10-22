import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { friendlyMessage } from '@/lib/api/errors'
import { resetPassword } from './api'
import { AuthLayout, FormAlert, Notice } from './AuthLayout'
import { applyFieldErrors } from './field-errors'
import { resetSchema, type ResetValues } from './schemas'

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  // Read the token once, then strip it from the address bar so it is not kept in history.
  const [token] = useState(() => params.get('token'))
  useEffect(() => {
    if (token) navigate('/reset-password', { replace: true })
  }, [token, navigate])
  const [done, setDone] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ResetValues>({ resolver: zodResolver(resetSchema) })

  if (!token) {
    return (
      <AuthLayout title="Choose a new password">
        <div className="flex flex-col gap-4">
          <FormAlert message="This link is invalid or has expired." />
          <Link to="/forgot-password" className="text-accent underline">
            Request a new link
          </Link>
        </div>
      </AuthLayout>
    )
  }

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await resetPassword(token, values.password)
      setDone(true)
    } catch (err) {
      if (applyFieldErrors(err, setError, ['password'])) return
      setFormError(friendlyMessage(err))
    }
  })

  if (done) {
    return (
      <AuthLayout title="Password updated">
        <div className="flex flex-col gap-4">
          <Notice>Your password was changed and you were signed out everywhere.</Notice>
          <Link to="/login" className="text-accent underline">
            Sign in
          </Link>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Choose a new password">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4" aria-busy={isSubmitting}>
        <FormAlert message={formError} />
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          error={errors.confirm?.message}
          {...register('confirm')}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Change password'}
        </Button>
      </form>
    </AuthLayout>
  )
}
