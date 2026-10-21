import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

const button = cva(
  'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-accent text-white hover:bg-accent-hover',
        secondary: 'bg-surface-2 text-text hover:bg-surface-3',
        ghost: 'bg-transparent text-text hover:bg-surface-2',
      },
      size: { sm: 'h-9 px-3 text-sm', md: 'h-11 px-4 text-base' },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

type Props = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof button>

export function Button({ variant, size, className, type = 'button', ...rest }: Props) {
  return <button type={type} className={cn(button({ variant, size }), className)} {...rest} />
}
