import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'
import { ErrorBoundary } from './ErrorBoundary'
import { Input } from './Input'

describe('Button', () => {
  it('calls onClick and defaults to type=button', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Play</Button>)
    const btn = screen.getByRole('button', { name: 'Play' })
    expect(btn).toHaveAttribute('type', 'button')
    await userEvent.click(btn)
    expect(onClick).toHaveBeenCalledOnce()
  })
})

describe('Input', () => {
  it('associates label and error with the field', () => {
    render(<Input label="Email" error="Required" />)
    const field = screen.getByLabelText('Email')
    expect(field).toHaveAttribute('aria-invalid', 'true')
    expect(field).toHaveAccessibleDescription('Required')
  })
})

describe('ErrorBoundary', () => {
  it('shows a fallback when a child throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const Boom = () => {
      throw new Error('boom')
    }
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })
})
