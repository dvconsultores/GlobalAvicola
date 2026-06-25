/**
 * Button — Global Avícola design system
 * Variants: primary | secondary | danger | ghost | outline
 * Sizes: sm | md | lg
 * Works on all modern browsers (Chrome, Edge, Firefox, Safari, Opera, iOS, Android)
 */
import { type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  children: ReactNode
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-[#2563EB] text-white hover:bg-[#1D4ED8] active:bg-[#1E40AF] focus-visible:ring-blue-400',
  secondary:
    'bg-[#F1F5F9] dark:bg-slate-700 text-[#334155] dark:text-slate-200 hover:bg-[#E2E8F0] dark:hover:bg-slate-600 active:bg-[#CBD5E1] focus-visible:ring-slate-400',
  danger:
    'bg-[#DC2626] text-white hover:bg-[#B91C1C] active:bg-[#991B1B] focus-visible:ring-red-400',
  ghost:
    'bg-transparent text-[#334155] dark:text-slate-300 hover:bg-[#F1F5F9] dark:hover:bg-slate-700 active:bg-[#E2E8F0] focus-visible:ring-slate-400',
  outline:
    'bg-transparent border border-[#E2E8F0] dark:border-slate-600 text-[#334155] dark:text-slate-300 hover:bg-[#F8FAFC] dark:hover:bg-slate-700 active:bg-[#F1F5F9] focus-visible:ring-slate-400',
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'h-11 px-4 text-sm gap-1.5',   // F-01: 44px minimum touch target
  md: 'h-11 px-5 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      disabled={isDisabled}
      className={[
        'inline-flex items-center justify-center font-medium rounded-lg',
        'transition-colors duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      ].join(' ')}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin shrink-0" />
      ) : leftIcon ? (
        <span className="shrink-0">{leftIcon}</span>
      ) : null}
      {children}
      {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  )
}
