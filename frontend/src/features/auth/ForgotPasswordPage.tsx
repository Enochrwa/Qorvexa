import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { friendlyMessage } from '@/lib/api/errors'
import { forgotPassword } from './api'
import { AuthLayout, FormAlert, Notice } from './AuthLayout'
import { forgotSchema, type ForgotValues } from './schemas'

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotValues>({ resolver: zodResolver(forgotSchema) })

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      await forgotPassword(values.email)
      setSent(true)
    } catch (err) {
      setFormError(friendlyMessage(err))
    }
  })

  return (
    <AuthLayout title="Reset your password">
      {sent ? (
        <div className="flex flex-col gap-4">
          <Notice>
            If an account exists for that email, we sent a link to reset the password.
          </Notice>
          <Link to="/login" className="text-accent underline">
            Back to sign in
          </Link>
        </div>
      ) : (
        <form
          onSubmit={onSubmit}
          noValidate
          className="flex flex-col gap-4"
          aria-busy={isSubmitting}
        >
          <FormAlert message={formError} />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending…' : 'Send reset link'}
          </Button>
          <Link to="/login" className="text-sm text-accent underline">
            Back to sign in
          </Link>
        </form>
      )}
    </AuthLayout>
  )
}
