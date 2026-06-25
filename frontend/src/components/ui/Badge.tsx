/**
 * Badge — Global Avícola design system
 * Variants match operational event statuses + generic states
 * Uses shared STATUS_STYLES from data/statusColors.ts (DIS-01)
 * All status labels resolved via i18n
 */
import { type ReactNode } from 'react'
import { STATUS_STYLES, resolveStatus, type StatusKey } from '../../data/statusColors'

type BadgeVariant = StatusKey

type BadgeSize = 'sm' | 'md'

interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  children: ReactNode
  className?: string
  dot?: boolean
}

const SIZE_CLASSES: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
}

/** Map API status string to Badge variant using shared resolveStatus */
export function statusToVariant(status: string): BadgeVariant {
  return resolveStatus(status)
}

export function Badge({
  variant = 'neutral',
  size = 'md',
  children,
  className = '',
  dot = false,
}: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1 rounded-full font-medium',
        STATUS_STYLES[variant]?.bg || 'bg-slate-100',
        STATUS_STYLES[variant]?.text || 'text-slate-600',
        SIZE_CLASSES[size],
        className,
      ].join(' ')}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_STYLES[variant]?.dot || 'bg-slate-400'}`} />
      )}
      {children}
    </span>
  )
}
