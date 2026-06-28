/**
 * Button — Global Avícola Corporate Design System v2
 * Variants: primary | secondary | danger | ghost | outline
 * Sizes: sm | md | lg
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
 'bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-700 focus-visible:ring-brand-400 shadow-sm hover:shadow-md',
 secondary:
 'bg-slate-100 dark:bg-slate-700 dark:bg-dark-card text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 active:bg-slate-300 focus-visible:ring-slate-400 border border-slate-200 dark:border-dark-border',
 danger:
 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus-visible:ring-red-400 shadow-sm hover:shadow-md',
 ghost:
 'bg-transparent text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-dark-card active:bg-slate-200 focus-visible:ring-slate-400',
 outline:
 'bg-transparent border border-slate-200 dark:border-dark-border text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-dark-card active:bg-slate-100 focus-visible:ring-slate-400',
}

const SIZE_CLASSES: Record<Size, string> = {
 sm: 'h-9 px-3.5 text-xs gap-1.5 rounded-lg',
 md: 'h-10 px-4 text-sm gap-2 rounded-xl',
 lg: 'h-11 px-5 text-sm gap-2 rounded-xl',
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
 'inline-flex items-center justify-center font-semibold',
 'transition-all duration-150',
 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
 'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none',
 VARIANT_CLASSES[variant],
 SIZE_CLASSES[size],
 className,
 ].join(' ')}
 {...props}
 >
 {loading ? (
 <Loader2 size={size === 'sm' ? 13 : 15} className="animate-spin shrink-0" />
 ) : leftIcon ? (
 <span className="shrink-0">{leftIcon}</span>
 ) : null}
 {children}
 {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
 </button>
 )
}

