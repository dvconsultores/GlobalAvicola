/**
 * Card — Global Avícola Corporate Design System v2
 * Clean, architectural card with shadow hierarchy
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
 default: 'bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700',
 flat: 'bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700',
 elevated: 'bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-card',
}

const PADDING_CLASSES = {
 none: '',
 sm: 'p-3',
 md: 'p-4',
 lg: 'p-5',
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
 <div className={`flex items-center justify-between gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-700 ${className}`}>
 <div>
 {typeof title === 'string' ? (
 <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">{title}</h3>
 ) : title}
 {subtitle && (
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{subtitle}</p>
 )}
 </div>
 {action && <div className="shrink-0 text-slate-400 dark:text-slate-500">{action}</div>}
 </div>
 )
}

export function CardBody({ children, className = '' }: CardBodyProps) {
 return (
 <div className={`px-4 py-3 ${className}`}>
 {children}
 </div>
 )
}

