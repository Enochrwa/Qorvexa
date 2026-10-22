import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { friendlyMessage } from '@/lib/api/errors'
import { login } from './api'
import { AuthLayout, FormAlert } from './AuthLayout'
import { applyFieldErrors } from './field-errors'
import { safeNext } from './safe-next'
import { loginSchema, type LoginValues } from './schemas'

export function LoginPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await login(values.email, values.password)
      navigate(safeNext(params.get('next')), { replace: true })
    } catch (err) {
      if (applyFieldErrors(err, setError, ['email', 'password'])) return
      setFormError(friendlyMessage(err, 'Incorrect email or password.'))
    }
  })

  return (
    <AuthLayout title="Sign in">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4" aria-busy={isSubmitting}>
        <FormAlert message={formError} />
        <Input
          label="Email"
          type="email"
          autoComplete="username"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </Button>
        <div className="flex justify-between text-sm">
          <Link to="/forgot-password" className="text-accent underline">
            Forgot password?
          </Link>
          <Link to="/register" className="text-accent underline">
            Create account
          </Link>
        </div>
      </form>
    </AuthLayout>
  )
}
