/**
 * Card — Global Avícola design system
 * Variants: default | flat | elevated
 * Optional header with title + action slot
 */
import { type ReactNode, type HTMLAttributes } from 'react'

type CardVariant = 'default' | 'flat' | 'elevated'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

interface CardHeaderProps {
  title: ReactNode
  subtitle?: ReactNode
  action?: ReactNode
  className?: string
}

interface CardBodyProps {
  children: ReactNode
  className?: string
}

const VARIANT_CLASSES: Record<CardVariant, string> = {
  default: 'bg-white border border-slate-200 shadow-sm',
  flat: 'bg-white border border-slate-200',
  elevated: 'bg-white shadow-md border border-slate-100',
}

const PADDING_CLASSES = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6',
}

export function Card({
  variant = 'default',
  padding = 'none',
  children,
  className = '',
  ...props
}: CardProps) {
  return (
    <div
      className={[
        'rounded-xl overflow-hidden',
        VARIANT_CLASSES[variant],
        padding !== 'none' ? PADDING_CLASSES[padding] : '',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action, className = '' }: CardHeaderProps) {
  return (
    <div className={`flex items-start justify-between gap-3 px-5 py-4 border-b border-slate-100 ${className}`}>
      <div>
        {typeof title === 'string' ? (
          <h3 className="font-semibold text-slate-800 text-sm">{title}</h3>
        ) : title}
        {subtitle && (
          <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}

export function CardBody({ children, className = '' }: CardBodyProps) {
  return (
    <div className={`px-5 py-4 ${className}`}>
      {children}
    </div>
  )
}
