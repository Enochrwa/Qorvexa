import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { friendlyMessage } from '@/lib/api/errors'
import { register as registerAccount } from './api'
import { AuthLayout, FormAlert, Notice } from './AuthLayout'
import { applyFieldErrors } from './field-errors'
import { registerSchema, type RegisterValues } from './schemas'

export function RegisterPage() {
  const [sentTo, setSentTo] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await registerAccount(values.email, values.password)
      setSentTo(values.email)
    } catch (err) {
      if (applyFieldErrors(err, setError, ['email', 'password'])) return
      setFormError(friendlyMessage(err))
    }
  })

  if (sentTo) {
    return (
      <AuthLayout title="Check your email">
        <div className="flex flex-col gap-4">
          <Notice>
            If {sentTo} can be registered, we sent a verification link to it. Open it to activate
            your account.
          </Notice>
          <Link to="/login" className="text-accent underline">
            Back to sign in
          </Link>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Create your account">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4" aria-busy={isSubmitting}>
        <FormAlert message={formError} />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          error={errors.confirm?.message}
          {...register('confirm')}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </Button>
        <p className="text-sm text-text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-accent underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
