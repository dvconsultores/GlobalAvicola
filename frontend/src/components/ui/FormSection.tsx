import { useState } from 'react'
import { ChevronDown, type LucideIcon } from 'lucide-react'

interface FormSectionProps {
 title: string
 description?: string
 icon?: LucideIcon
 /** Color del icono (clase Tailwind) */
 iconColor?: string
 /** Por defecto abierto */
 defaultOpen?: boolean
 /** Permitir colapsar */
 collapsible?: boolean
 children: React.ReactNode
 className?: string
}

/**
 * FormSection — Sección visual para formularios con título, icono y contenido.
 *
 * Útil para agrupar campos relacionados en formularios largos.
 * Soporta modo colapsable para mobile.
 */
export default function FormSection({
 title,
 description,
 icon: Icon,
 iconColor = 'text-blue-600',
 defaultOpen = true,
 collapsible = false,
 children,
 className = '',
}: FormSectionProps) {
 const [open, setOpen] = useState(defaultOpen)

 return (
 <div className={`border border-slate-200 rounded-xl bg-white dark:bg-slate-800 overflow-hidden ${className}`}>
 {/* Header */}
 <div
 className={`flex items-center gap-2.5 px-4 py-3 border-b border-slate-100 ${
 collapsible ? 'cursor-pointer hover:bg-slate-50 select-none' : ''
 }`}
 onClick={collapsible ? () => setOpen(!open) : undefined}
 >
 {Icon && (
 <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800 flex items-center justify-center">
 <Icon size={16} className={iconColor} />
 </div>
 )}
 <div className="flex-1 min-w-0">
 <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">{title}</h3>
 {description && (
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{description}</p>
 )}
 </div>
 {collapsible && (
 <ChevronDown
 size={16}
 className={`text-slate-400 dark:text-slate-500 transition-transform duration-200 ${
 open ? 'rotate-0' : '-rotate-90'
 }`}
 />
 )}
 </div>

 {/* Content */}
 <div
 className={`transition-all duration-200 ease-in-out ${
 collapsible && !open ? 'max-h-0 opacity-0 overflow-hidden' : 'max-h-[2000px] opacity-100'
 }`}
 >
 <div className="p-4 space-y-3">
 {children}
 </div>
 </div>
 </div>
 )
}
