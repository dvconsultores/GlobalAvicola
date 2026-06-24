/**
 * Badge — Global Avícola design system
 * Variants match the 13 operational event statuses + generic states
 * All status labels resolved via i18n
 */
import { type ReactNode } from 'react'

type BadgeVariant =
  | 'approved' | 'pending' | 'rejected' | 'in_review' | 'returned'
  | 'corrected' | 'consolidated' | 'sent_sap' | 'confirmed_sap' | 'error_sap'
  | 'draft' | 'registered' | 'cancelled'
  | 'info' | 'warning' | 'neutral'

type BadgeSize = 'sm' | 'md'

interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  children: ReactNode
  className?: string
  dot?: boolean
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  // Operational states
  draft:       'bg-slate-100 text-slate-600',
  registered:  'bg-blue-100 text-blue-700',
  pending:     'bg-yellow-100 text-yellow-700',
  in_review:   'bg-blue-100 text-blue-700',
  returned:    'bg-orange-100 text-orange-700',
  corrected:   'bg-purple-100 text-purple-700',
  rejected:    'bg-red-100 text-red-700',
  approved:    'bg-emerald-100 text-emerald-700',
  consolidated:'bg-teal-100 text-teal-700',
  sent_sap:    'bg-indigo-100 text-indigo-700',
  confirmed_sap: 'bg-emerald-100 text-emerald-800',
  error_sap:   'bg-red-100 text-red-700',
  cancelled:   'bg-slate-100 text-slate-500',
  // Generic
  info:    'bg-blue-100 text-blue-700',
  warning: 'bg-yellow-100 text-yellow-700',
  neutral: 'bg-slate-100 text-slate-600',
}

const DOT_CLASSES: Record<BadgeVariant, string> = {
  draft:        'bg-slate-400',
  registered:   'bg-blue-500',
  pending:      'bg-yellow-500',
  in_review:    'bg-blue-500',
  returned:     'bg-orange-500',
  corrected:    'bg-purple-500',
  rejected:     'bg-red-500',
  approved:     'bg-emerald-500',
  consolidated: 'bg-teal-500',
  sent_sap:     'bg-indigo-500',
  confirmed_sap:'bg-emerald-600',
  error_sap:    'bg-red-500',
  cancelled:    'bg-slate-400',
  info:    'bg-blue-500',
  warning: 'bg-yellow-500',
  neutral: 'bg-slate-400',
}

const SIZE_CLASSES: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
}

/** Map API status string to Badge variant */
export function statusToVariant(status: string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    draft: 'draft',
    registered: 'registered',
    pending_review: 'pending',
    in_review: 'in_review',
    returned: 'returned',
    corrected: 'corrected',
    rejected: 'rejected',
    approved: 'approved',
    consolidated: 'consolidated',
    sent_to_sap: 'sent_sap',
    confirmed_sap: 'confirmed_sap',
    error_sap: 'error_sap',
    cancelled: 'cancelled',
    active: 'approved',
    closed: 'neutral',
  }
  return map[status] ?? 'neutral'
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
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      ].join(' ')}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${DOT_CLASSES[variant]}`} />
      )}
      {children}
    </span>
  )
}
